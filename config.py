import dataclasses
from dataclasses import dataclass
from typing import Dict

@dataclass
class Config:
    out_dir: str = "patches"
    min_size: int = 16 
    png_preview: bool = True
    csv_name: str = "patches.csv"
    overlay_linewidth: float = 2.0
    overlay_color: str = "lime"
    labels: list[str] = dataclasses.field(default_factory=list)
    stretch_mode: str = "zscale"
    # New: Color mapping for labels
    label_colors: Dict[str, str] = dataclasses.field(default_factory=lambda: {
        "default": "lime",
        "star": "cyan",
        "galaxy": "magenta",
        "artifact": "yellow"
    })

    def get_color_for_label(self, label):
        return self.label_colors.get(label, self.label_colors["default"])