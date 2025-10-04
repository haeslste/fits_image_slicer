
from dataclasses import dataclass

@dataclass
class Config:
    out_dir: str = "patches"
    min_size: int = 16 
    png_preview: bool = True
    display_zscale: bool = True
    csv_name: str = "patches.csv"
    overlay_color: str = "lime"
    overlay_linewidth: float = 1.0