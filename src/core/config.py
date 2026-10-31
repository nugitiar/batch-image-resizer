"""Application configuration, constants, and data models.

Defines supported image formats, aspect ratios, scale multipliers,
resize filters, and dataclasses used across Windows, macOS, and Linux.

Author: Nugi Tiartanto (@nugitiar)
Role:   Informatics Student & Independent Software Developer
GitHub: https://github.com/nugitiar
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# Supported File Formats
# ==============================================================================
SUPPORTED_EXTENSIONS: Tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".tiff",
    ".tif",
    ".heic",
    ".bmp",
    ".avif",
)

# ==============================================================================
# Aspect Ratios: name -> (width_ratio, height_ratio) or None for no crop
# ==============================================================================
@dataclass(frozen=True)
class AspectRatioOption:
    id: str
    label: str
    ratio: Optional[Tuple[int, int]]  # (w, h) or None if original ratio


ASPECT_RATIOS: Dict[str, AspectRatioOption] = {
    "original": AspectRatioOption(
        id="original",
        label="Original Ratio (No Crop)",
        ratio=None,
    ),
    "1:1": AspectRatioOption(
        id="1:1",
        label="Square (1:1)",
        ratio=(1, 1),
    ),
    "4:3": AspectRatioOption(
        id="4:3",
        label="Landscape (4:3)",
        ratio=(4, 3),
    ),
    "3:4": AspectRatioOption(
        id="3:4",
        label="Portrait (3:4)",
        ratio=(3, 4),
    ),
    "16:9": AspectRatioOption(
        id="16:9",
        label="Widescreen (16:9)",
        ratio=(16, 9),
    ),
    "9:16": AspectRatioOption(
        id="9:16",
        label="Vertical (9:16)",
        ratio=(9, 16),
    ),
}

# ==============================================================================
# Scale Multipliers: name -> multiplier float
# ==============================================================================
@dataclass(frozen=True)
class ScaleOption:
    id: str
    label: str
    multiplier: float


SCALE_MULTIPLIERS: Dict[str, ScaleOption] = {
    "1x": ScaleOption(id="1x", label="1x (Original Size)", multiplier=1.0),
    "2x": ScaleOption(id="2x", label="2x (200%)", multiplier=2.0),
    "3x": ScaleOption(id="3x", label="3x (300%)", multiplier=3.0),
    "4x": ScaleOption(id="4x", label="4x (400%)", multiplier=4.0),
}

# ==============================================================================
# Resize Quality Algorithms (ImageMagick -filter)
# ==============================================================================
@dataclass(frozen=True)
class FilterOption:
    id: str
    label: str
    filter_name: str
    description: str


RESIZE_FILTERS: Dict[str, FilterOption] = {
    "Lanczos": FilterOption(
        id="Lanczos",
        label="Lanczos (Recommended: High Sharpness & Detail)",
        filter_name="Lanczos",
        description="Sinc-windowed filter, superior detail retention for upscaling",
    ),
    "Cubic": FilterOption(
        id="Cubic",
        label="Bicubic / Cubic (Smooth photographic resample)",
        filter_name="Cubic",
        description="Standard bicubic interpolation, smooth gradients",
    ),
    "Mitchell": FilterOption(
        id="Mitchell",
        label="Mitchell-Netravali (Balanced / Minimal Ringing)",
        filter_name="Mitchell",
        description="Balanced cubic filter reducing edge ringing artifacts",
    ),
    "Catrom": FilterOption(
        id="Catrom",
        label="Catmull-Rom (Sharp Cubic)",
        filter_name="Catrom",
        description="Modified cubic spline with sharp transition boundaries",
    ),
    "Triangle": FilterOption(
        id="Triangle",
        label="Bilinear / Triangle (Fast interpolation)",
        filter_name="Triangle",
        description="Linear interpolation, faster processing speed",
    ),
    "Point": FilterOption(
        id="Point",
        label="Nearest Neighbor / Point (Pixel Art / Hard Edges)",
        filter_name="Point",
        description="Replicates nearest pixel, ideal for pixel art without blurring",
    ),
}

# ==============================================================================
# Processing Options & Result Dataclasses
# ==============================================================================
@dataclass
class ProcessingOptions:
    input_paths: List[Path]
    output_dir: Path
    scale: ScaleOption
    aspect_ratio: AspectRatioOption
    filter_option: FilterOption
    output_format: str = "original"  # "original", "png", "jpg", "webp"
    jpeg_quality: int = 92
    concurrency: int = 4
    overwrite_existing: bool = True
    preserve_metadata: bool = True


@dataclass
class ProcessResult:
    input_path: Path
    output_path: Optional[Path]
    success: bool
    original_size: Optional[Tuple[int, int]] = None
    final_size: Optional[Tuple[int, int]] = None
    execution_time_seconds: float = 0.0
    error_message: Optional[str] = None
    command_executed: Optional[List[str]] = None
