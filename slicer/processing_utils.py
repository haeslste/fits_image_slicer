
import logging
from typing import Tuple
import numpy as np
from config import Config

def compute_integer_bounds(
    xmin: float, ymin: float, xmax: float, ymax: float
) -> Tuple[int, int, int, int]:
    return (
        int(np.floor(xmin)),
        int(np.floor(ymin)),
        int(np.ceil(xmax)),
        int(np.ceil(ymax)),
    )


def size_ok(ix0: int, iy0: int, ix1: int, iy1: int, cfg: Config) -> bool:
    w, h = ix1 - ix0, iy1 - iy0
    if w < cfg.min_size or h < cfg.min_size:
        logging.info(f"Ignored: too small ({w}x{h} < {cfg.min_size})")
        return False
    return True


def in_img_bounds(
    ix0: int, iy0: int, ix1: int, iy1: int, shape: Tuple[int, int]
) -> bool:
    H, W = shape
    if ix0 < 0 or iy0 < 0 or ix1 > W or iy1 > H:
        logging.info("Ignored: rectangle extends outside image bounds.")
        return False
    return True