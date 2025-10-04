# fits_patch_picker.py
import os
import sys
import csv
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle
from matplotlib import image as mpimg

                
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.wcs import WCS
from astropy.visualization import ZScaleInterval, AsinhStretch, ImageNormalize
from processing_utils import compute_integer_bounds, size_ok, in_img_bounds
from config import Config

# Optional file dialog
try:
    import tkinter as tk
    from tkinter import filedialog

    TK_OK = True
    print("Tkinter available, file dialog will be enabled.")
except Exception:
    print("Tkinter not available, file dialog will be disabled.")
    TK_OK = False

# ---------------------------- Config ---------------------------------
CFG = Config()
print(f"Using configuration: {CFG}")

# ---------------------------- Utils ----------------------------------

def setup_logging() -> None:
    """Setup basic logging configuration."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def load_fits_2d(path: str) -> Tuple[np.ndarray, fits.Header, WCS]:
    data = fits.getdata(path)
    if data is None or np.asarray(data).ndim != 2:
        raise ValueError("Only 2D FITS images supported.")
    hdr = fits.getheader(path)
    wcs = WCS(hdr)
    return np.asarray(data), hdr, wcs


def ensure_out_dir(cfg: Config) -> str:
    if os.path.exists(cfg.out_dir) and not os.path.isdir(cfg.out_dir):
        raise RuntimeError(f"{cfg.out_dir} exists and is not a directory.")
    os.makedirs(cfg.out_dir, exist_ok=True)
    return cfg.out_dir


def csv_init_if_needed(csv_path: str) -> None:
    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
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
                ]
            )


def next_patch_index(out_dir: str) -> int:
    nums = []
    for f in os.listdir(out_dir):
        if f.startswith("patch_") and f.endswith(".fits"):
            try:
                nums.append(int(f.split("_")[1].split(".")[0]))
            except Exception:
                pass
    return (max(nums) + 1) if nums else 1





def make_cutout(
    data: np.ndarray, wcs: WCS, ix0: int, iy0: int, ix1: int, iy1: int
) -> Cutout2D:
    w, h = ix1 - ix0, iy1 - iy0
    position = (ix0 + w / 2.0, iy0 + h / 2.0)  # (x, y) center in pixels
    size = (h, w)  # (ny, nx)
    return Cutout2D(data, position=position, size=size, wcs=wcs, mode="partial")


def save_fits_patch(
    cut: Cutout2D,
    base_hdr: fits.Header,
    out_path: str,
    src_name: str,
    ix0: int,
    iy0: int,
    ix1: int,
    iy1: int,
    dtype,
) -> None:
    hdr_out = base_hdr.copy()
    for k, v in cut.wcs.to_header().items():
        hdr_out[k] = v
    hdr_out["HISTORY"] = f"Cutout from {src_name} x=[{ix0}:{ix1}) y=[{iy0}:{iy1})"
    fits.PrimaryHDU(data=cut.data.astype(dtype, copy=False), header=hdr_out).writeto(
        out_path, overwrite=True
    )


def save_png_preview(cut: Cutout2D, out_png: str) -> None:
    fig, ax = plt.subplots(figsize=(3, 3))
    norm = ImageNormalize(cut.data, interval=ZScaleInterval(), stretch=AsinhStretch())
    ax.imshow(cut.data, origin="lower", cmap="gray", norm=norm)
    ax.axis("off")
    fig.savefig(out_png, dpi=200, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def append_csv(csv_path: str, row: List) -> None:
    with open(csv_path, "a", newline="") as f:
        csv.writer(f).writerow(row)


# ---------------------------- Main UI --------------------------------


class PatchPicker:
    def __init__(self, fits_path: str, cfg: Config = CFG):
        setup_logging()
        self.cfg = cfg
        if not fits_path:
            fits_path = self._pick_fits_path()
        if not fits_path:
            logging.error("No FITS file selected.")
            sys.exit(1)
        self.fits_path = fits_path
        self.data, self.hdr, self.wcs = load_fits_2d(fits_path)
        ensure_out_dir(cfg)
        self.csv_path = os.path.join(cfg.out_dir, cfg.csv_name)
        csv_init_if_needed(self.csv_path)
        self.counter = next_patch_index(cfg.out_dir)
        self.overlays: List[Rectangle] = []
        self.patches_meta: List[dict] = []
        self.cbar = None
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self._init_display()

        try:
            self.selector = RectangleSelector(
                self.ax, self.on_select,
                useblit=False,            # <- was True
                button=[1],
                interactive=False,
                minspanx=1, minspany=1,
                spancoords="pixels",
            )
        except TypeError:
            self.selector = RectangleSelector(
                self.ax, self.on_select,
                drawtype="box",
                useblit=False,            # <- was True
                button=[1],
                interactive=False,
                minspanx=1, minspany=1,
                spancoords="pixels",
            )
            
        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.ax.set_title(os.path.basename(fits_path) + "  |  drag to save patch")
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def _pick_fits_path() -> Optional[str]:
        if TK_OK:
            root = tk.Tk(); root.withdraw()
            path = filedialog.askopenfilename(
                title="Select FITS file",
                filetypes=[("FITS files","*.fits *.fit *.fz"), ("All files","*.*")]
            )
            root.update(); root.destroy()
            return path
        else:
            logging.info("Usage: python fits_patch_picker.py /path/to/image.fits")
            return None

    # ----- display -----
    def _init_display(self) -> None:
        self.ax.clear()
        if self.cbar:
            self.cbar.remove()
        #self.cbar = self.fig.colorbar(self.data, ax=self.ax, fraction=0.046, pad=0.04)
            
        if self.cfg.display_zscale:
            norm = ImageNormalize(
                self.data, interval=ZScaleInterval(), stretch=AsinhStretch()
            )
            self.im = self.ax.imshow(self.data, origin="lower", cmap="gray", norm=norm)
        else:
            self.im = self.ax.imshow(self.data, origin="lower", cmap="gray")
        self.ax.set_xlabel("X [pix]")
        self.ax.set_ylabel("Y [pix]")
        self.fig.colorbar(self.im, ax=self.ax, fraction=0.046, pad=0.04)
        for r in self.overlays:
            self.ax.add_patch(r)
        self.fig.canvas.draw_idle()

    # ----- events -----
    def on_select(self, eclick, erelease) -> None:
        x0, y0, x1, y1 = eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata
        if None in (x0, y0, x1, y1):
            return
        xmin, xmax = sorted([x0, x1])
        ymin, ymax = sorted([y0, y1])

        ix0, iy0, ix1, iy1 = compute_integer_bounds(xmin, ymin, xmax, ymax)
        if not size_ok(ix0, iy0, ix1, iy1, self.cfg):
            return
        if not in_img_bounds(ix0, iy0, ix1, iy1, self.data.shape):
            return

        w, h = ix1 - ix0, iy1 - iy0
        try:
            cut = make_cutout(self.data, self.wcs, ix0, iy0, ix1, iy1)
        except Exception as e:
            logging.info(f"Cutout failed: {e}")
            return

        patch_id = f"{self.counter:04d}"
        base = f"patch_{patch_id}"
        fits_out = os.path.join(self.cfg.out_dir, base + ".fits")
        save_fits_patch(
            cut,
            self.hdr,
            fits_out,
            os.path.basename(self.fits_path),
            ix0,
            iy0,
            ix1,
            iy1,
            self.data.dtype,
        )

        if self.cfg.png_preview:
            try:
                norm = ImageNormalize(cut.data, interval=ZScaleInterval(), stretch=AsinhStretch())
                arr = norm(cut.data)  # 0..1 float
                mpimg.imsave(
                    os.path.join(self.cfg.out_dir, f"patch_{patch_id}.png"),
                    arr, cmap="gray", origin="lower", dpi=200
                )
            except Exception as e:
                logging.info(f"Preview export failed: {e}")

        # CSV: compute celestial center using cutout-local center
        cx = cut.data.shape[1] / 2.0
        cy = cut.data.shape[0] / 2.0
        wc_center = cut.wcs.pixel_to_world(cx, cy)
        ra = getattr(wc_center, "ra", None)
        dec = getattr(wc_center, "dec", None)
        ra_deg = getattr(ra, "deg", "") if ra is not None else ""
        dec_deg = getattr(dec, "deg", "") if dec is not None else ""
        timestamp = np.datetime64('now').astype(str)
        append_csv(
            self.csv_path,
            [patch_id, timestamp, self.fits_path, ix0, iy0, ix1, iy1, w, h, ra_deg, dec_deg],
        )

        # overlay
        rect = Rectangle(
            (ix0, iy0),
            w,
            h,
            fill=False,
            edgecolor=self.cfg.overlay_color,
            linewidth=self.cfg.overlay_linewidth,
        )
        self.ax.add_patch(rect)
        self.overlays.append(rect)
        self.patches_meta.append({"id": patch_id, "fits": fits_out})
        self.counter += 1
        self.fig.canvas.draw_idle()
        logging.info(
            f"Saved patch {patch_id}: {w}x{h} @ x=[{ix0}:{ix1}) y=[{iy0}:{iy1})"
        )

    def on_key(self, event) -> None:
        if event.key == "q":
            plt.close(self.fig)
        elif event.key == "u":
            self.undo_last()
        elif event.key == "c":
            self.clear_overlays()
        elif event.key == "z":
            self.cfg.display_zscale = not self.cfg.display_zscale


patch_picker = PatchPicker(
    fits_path=sys.argv[1] if len(sys.argv) > 1 else "",
    cfg=CFG
) if TK_OK else None