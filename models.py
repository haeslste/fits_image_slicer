
import os
import csv
import logging
from typing import List, Tuple, Optional

import numpy as np
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy_importer import WCS
from astropy.visualization import (
    ZScaleInterval, AsinhStretch, ImageNormalize,
    LinearStretch, LogStretch, MinMaxInterval
)
from skimage.exposure import equalize_hist

from PIL import Image

from config import Config
from processing_utils import compute_integer_bounds, size_ok, in_img_bounds

class FitsImageModel:
    def __init__(self, fits_path: str):
        self.fits_path = fits_path
        self.data, self.hdr, self.wcs = self._load_fits_2d(fits_path)

    def _load_fits_2d(self, path: str) -> Tuple[np.ndarray, fits.Header, WCS]:
        data = fits.getdata(path)
        if data is None or np.asarray(data).ndim != 2:
            raise ValueError("Only 2D FITS images supported.")
        hdr = fits.getheader(path)
        wcs = WCS(hdr)
        return np.asarray(data), hdr, wcs

    def get_normalized_image_data(self, stretch_mode: str = "zscale") -> np.ndarray:
        data_for_norm = np.nan_to_num(self.data)

        if stretch_mode == "histeq":
            img_min, img_max = np.min(data_for_norm), np.max(data_for_norm)
            if img_max > img_min:
                data_for_norm = (data_for_norm - img_min) / (img_max - img_min)
            return equalize_hist(data_for_norm)

        stretch = AsinhStretch()
        interval = ZScaleInterval()

        if stretch_mode == "linear":
            stretch = LinearStretch()
            interval = MinMaxInterval()
        elif stretch_mode == "log":
            stretch = LogStretch()
            interval = MinMaxInterval()

        norm = ImageNormalize(data_for_norm, interval=interval, stretch=stretch)
        normalized_data = norm(data_for_norm)
        
        if hasattr(normalized_data, 'filled'):
            normalized_data = normalized_data.filled(0)
            
        return normalized_data

class PatchExporter:
    def __init__(self, cfg: Config, fits_image_model: FitsImageModel):
        self.cfg = cfg
        self.fits_image_model = fits_image_model
        self.out_dir = self._ensure_out_dir()
        self.csv_path = os.path.join(self.out_dir, self.cfg.csv_name)
        self._csv_init_if_needed()
        self.counter = self._next_patch_index()
        self.patches_meta: List[dict] = []

    def _ensure_out_dir(self) -> str:
        if os.path.exists(self.cfg.out_dir) and not os.path.isdir(self.cfg.out_dir):
            raise RuntimeError(f"{self.cfg.out_dir} exists and is not a directory.")
        os.makedirs(self.cfg.out_dir, exist_ok=True)
        return self.cfg.out_dir

    def _csv_init_if_needed(self) -> None:
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(
                    [
                        "patch_id",
                        "timestamp",
                        "fits_path",
                        "x0",
                        "y0",
                        "x1",
                        "y1",
                        "width",
                        "height",
                        "ra_deg_cen",
                        "dec_deg_cen",
                        "label",
                    ]
                )

    def _next_patch_index(self) -> int:
        nums = []
        for f in os.listdir(self.out_dir):
            if f.startswith("patch_") and f.endswith(".fits"):
                try:
                    nums.append(int(f.split("_")[1].split(".")[0]))
                except Exception:
                    pass
        return (max(nums) + 1) if nums else 1

    def save_patch(self, xmin: float, ymin: float, xmax: float, ymax: float, label: str = None) -> Optional[dict]:
        ix0, iy0, ix1, iy1 = compute_integer_bounds(xmin, ymin, xmax, ymax)
        if not size_ok(ix0, iy0, ix1, iy1, self.cfg):
            return None
        if not in_img_bounds(ix0, iy0, ix1, iy1, self.fits_image_model.data.shape):
            return None

        w, h = ix1 - ix0, iy1 - iy0
        try:
            cut = self._make_cutout(ix0, iy0, ix1, iy1)
        except Exception as e:
            logging.info(f"Cutout failed: {e}")
            return None

        patch_id = f"{self.counter:04d}"
        self._save_fits_patch(cut, patch_id, ix0, iy0, ix1, iy1)

        if self.cfg.png_preview:
            self._save_png_preview(cut, patch_id)

        patch_meta = self._get_patch_metadata(cut, patch_id, ix0, iy0, ix1, iy1, w, h, label)
        self._append_csv(patch_meta)
        self.patches_meta.append(patch_meta)

        self.counter += 1
        logging.info(
            f"Saved patch {patch_id}: {w}x{h} @ x=[{ix0}:{ix1}) y=[{iy0}:{iy1})"
        )
        return patch_meta

    def _make_cutout(self, ix0: int, iy0: int, ix1: int, iy1: int) -> Cutout2D:
        w, h = ix1 - ix0, iy1 - iy0
        position = (ix0 + w / 2.0, iy0 + h / 2.0)
        size = (h, w)
        return Cutout2D(
            self.fits_image_model.data,
            position=position,
            size=size,
            wcs=self.fits_image_model.wcs,
            mode="partial",
        )

    def _save_fits_patch(self, cut: Cutout2D, patch_id: str, ix0: int, iy0: int, ix1: int, iy1: int) -> None:
        base = f"patch_{patch_id}"
        fits_out = os.path.join(self.out_dir, base + ".fits")
        hdr_out = self.fits_image_model.hdr.copy()
        for k, v in cut.wcs.to_header().items():
            hdr_out[k] = v
        hdr_out["HISTORY"] = f"Cutout from {os.path.basename(self.fits_image_model.fits_path)} x=[{ix0}:{ix1}) y=[{iy0}:{iy1})"
        fits.PrimaryHDU(
            data=cut.data.astype(self.fits_image_model.data.dtype, copy=False),
            header=hdr_out,
        ).writeto(fits_out, overwrite=True)

    def _save_png_preview(self, cut: Cutout2D, patch_id: str) -> None:
        try:
            norm = ImageNormalize(cut.data, interval=ZScaleInterval(), stretch=AsinhStretch())
            arr = norm(cut.data)
            arr = (arr * 255).astype(np.uint8)
            img = Image.fromarray(arr, mode='L')
            img.save(os.path.join(self.out_dir, f"patch_{patch_id}.png"))
        except Exception as e:
            logging.info(f"Preview export failed: {e}")

    def _get_patch_metadata(self, cut: Cutout2D, patch_id: str, ix0: int, iy0: int, ix1: int, iy1: int, w: int, h: int, label: str = None) -> dict:
        cx = cut.data.shape[1] / 2.0
        cy = cut.data.shape[0] / 2.0
        wc_center = cut.wcs.pixel_to_world(cx, cy)
        ra = getattr(wc_center, "ra", None)
        dec = getattr(wc_center, "dec", None)
        ra_deg = getattr(ra, "deg", "") if ra is not None else ""
        dec_deg = getattr(dec, "deg", "") if dec is not None else ""
        timestamp = np.datetime64("now").astype(str)
        
        return {
            "patch_id": patch_id,
            "timestamp": timestamp,
            "fits_path": self.fits_image_model.fits_path,
            "x0": ix0,
            "y0": iy0,
            "x1": ix1,
            "y1": iy1,
            "width": w,
            "height": h,
            "ra_deg_cen": ra_deg,
            "dec_deg_cen": dec_deg,
            "label": label,
        }

    def _append_csv(self, patch_meta: dict) -> None:
        with open(self.csv_path, "a", newline="") as f:
            csv.writer(f).writerow(patch_meta.values())

    def undo_last_patch(self) -> None:
        if not self.patches_meta:
            return

        last_patch = self.patches_meta.pop()
        patch_id = last_patch["patch_id"]

        # Remove patch files
        base = f"patch_{patch_id}"
        fits_out = os.path.join(self.out_dir, base + ".fits")
        png_out = os.path.join(self.out_dir, base + ".png")
        if os.path.exists(fits_out):
            os.remove(fits_out)
        if os.path.exists(png_out):
            os.remove(png_out)

        # Rewrite CSV without the last patch
        all_patches = []
        with open(self.csv_path, "r", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            all_patches.append(header)
            for row in reader:
                if row[0] != patch_id:
                    all_patches.append(row)

        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(all_patches)

        self.counter -= 1
        logging.info(f"Undid patch {patch_id}")

    def clear_all_patches(self) -> None:
        for patch in self.patches_meta:
            patch_id = patch["patch_id"]
            base = f"patch_{patch_id}"
            fits_out = os.path.join(self.out_dir, base + ".fits")
            png_out = os.path.join(self.out_dir, base + ".png")
            if os.path.exists(fits_out):
                os.remove(fits_out)
            if os.path.exists(png_out):
                os.remove(png_out)

        self.patches_meta = []
        self._csv_init_if_needed()  # This will effectively clear the CSV
        self.counter = 1
        logging.info("Cleared all patches")
