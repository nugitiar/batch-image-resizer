"""Core processing engine and ImageMagick interfaces."""

from .config import (
    ASPECT_RATIOS,
    SCALE_MULTIPLIERS,
    RESIZE_FILTERS,
    SUPPORTED_EXTENSIONS,
    ProcessingOptions,
    ProcessResult,
)
from .detector import ImageMagickDetector, ImageMagickInfo
from .processor import ImageProcessor
from .worker import BatchWorker, BatchSummary

__all__ = [
    "ASPECT_RATIOS",
    "SCALE_MULTIPLIERS",
    "RESIZE_FILTERS",
    "SUPPORTED_EXTENSIONS",
    "ProcessingOptions",
    "ProcessResult",
    "ImageMagickDetector",
    "ImageMagickInfo",
    "ImageProcessor",
    "BatchWorker",
    "BatchSummary",
]
