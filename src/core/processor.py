"""Cross-Platform Image processing engine using ImageMagick CLI.

Handles dimension probing, aspect ratio crop calculations, filter selection,
scaling, and safe subprocess execution across Windows, macOS, and Linux.

Author: Nugi Tiartanto (@nugitiar)
"""

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import List, Optional, Tuple

from .config import (
    AspectRatioOption,
    FilterOption,
    ProcessingOptions,
    ProcessResult,
    ScaleOption,
)
from .detector import ImageMagickInfo


class ImageProcessor:
    """Executes image resizing, aspect-ratio cropping, and upscaling via ImageMagick."""

    def __init__(self, magick_info: ImageMagickInfo):
        if not magick_info.is_available or not magick_info.binary_path:
            raise ValueError(f"ImageMagick is unavailable: {magick_info.error_message}")
        self.magick_path: Path = magick_info.binary_path
        self.is_im7: bool = magick_info.is_imagemagick_7

    def _get_subprocess_extra_kwargs(self) -> dict:
        """Returns platform-specific subprocess creation flags.

        On Windows: sets CREATE_NO_WINDOW to eliminate command prompt flashing during batch runs.
        """
        extra = {}
        if sys.platform == "win32":
            extra["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        return extra

    def get_image_dimensions(self, image_path: Path) -> Tuple[int, int]:
        """Probes the pixel width and height of an image file.

        Uses: magick identify -format "%w %h" "image_path[0]"
        """
        # Specify [0] to select first layer/frame for multi-page TIFFs or animated GIFs
        target_spec = f"{image_path}[0]"
        if self.is_im7:
            cmd = [str(self.magick_path), "identify", "-format", "%w %h", target_spec]
        else:
            # Legacy ImageMagick 6 fallback
            identify_bin = self.magick_path.parent / ("identify.exe" if sys.platform == "win32" else "identify")
            if identify_bin.is_file() and (sys.platform == "win32" or os.access(identify_bin, os.X_OK)):
                cmd = [str(identify_bin), "-format", "%w %h", target_spec]
            else:
                cmd = [str(self.magick_path), "-format", "%w %h", target_spec]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=15.0,
                **self._get_subprocess_extra_kwargs(),
            )
            output = result.stdout.strip()
            parts = output.split()
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
            raise ValueError(f"Unexpected identify output: '{output}'")
        except subprocess.SubprocessError as exc:
            stderr = getattr(exc, "stderr", "")
            raise RuntimeError(
                f"Failed to probe image dimensions for '{image_path.name}': {stderr or exc}"
            ) from exc

    @staticmethod
    def calculate_crop_dimensions(
        width: int,
        height: int,
        target_ratio: Optional[Tuple[int, int]],
    ) -> Tuple[int, int]:
        """Calculates center-crop bounding box to achieve the target aspect ratio.

        Args:
            width: Current image width in pixels.
            height: Current image height in pixels.
            target_ratio: (w_ratio, h_ratio) tuple or None for no crop.

        Returns:
            Tuple of (crop_width, crop_height).
        """
        if not target_ratio or width <= 0 or height <= 0:
            return width, height

        rw, rh = target_ratio
        target_aspect = rw / rh
        current_aspect = width / height

        # Within floating point tolerance, no crop needed
        if abs(current_aspect - target_aspect) < 1e-4:
            return width, height

        if current_aspect > target_aspect:
            # Image is wider than desired ratio -> trim horizontal sides
            crop_height = height
            crop_width = int(round(height * target_aspect))
            crop_width = min(crop_width, width)
        else:
            # Image is taller than desired ratio -> trim top/bottom
            crop_width = width
            crop_height = int(round(width / target_aspect))
            crop_height = min(crop_height, height)

        return crop_width, crop_height

    def build_command(
        self,
        input_path: Path,
        output_path: Path,
        orig_width: int,
        orig_height: int,
        scale: ScaleOption,
        aspect_ratio: AspectRatioOption,
        filter_opt: FilterOption,
        output_format: str = "original",
        jpeg_quality: int = 92,
    ) -> Tuple[List[str], Tuple[int, int]]:
        """Constructs safe argument list for ImageMagick CLI invocation."""
        cmd: List[str] = [str(self.magick_path)]

        # Input file
        cmd.append(str(input_path))

        # Respect EXIF orientation tag before cropping/scaling
        cmd.append("-auto-orient")

        # 1. Aspect Ratio Cropping
        crop_w, crop_h = self.calculate_crop_dimensions(
            orig_width, orig_height, aspect_ratio.ratio
        )
        needs_crop = (crop_w != orig_width) or (crop_h != orig_height)

        if needs_crop:
            cmd.extend([
                "-gravity", "center",
                "-crop", f"{crop_w}x{crop_h}+0+0",
                "+repage",
            ])

        # 2. Resampling Filter & Scale Multiplier
        final_w = int(round(crop_w * scale.multiplier))
        final_h = int(round(crop_h * scale.multiplier))

        if scale.multiplier != 1.0:
            cmd.extend([
                "-filter", filter_opt.filter_name,
                "-resize", f"{int(round(scale.multiplier * 100))}%",
            ])

        # 3. Compression / Quality for Lossy Formats
        target_ext = output_path.suffix.lower()
        if target_ext in (".jpg", ".jpeg", ".webp"):
            cmd.extend(["-quality", str(max(1, min(100, jpeg_quality)))])

        # Output file
        cmd.append(str(output_path))

        return cmd, (final_w, final_h)

    def determine_output_path(
        self,
        input_path: Path,
        output_dir: Path,
        scale: ScaleOption,
        aspect_ratio: AspectRatioOption,
        output_format: str = "original",
        overwrite: bool = True,
    ) -> Path:
        """Generates destination file path with intuitive suffix and format."""
        stem = input_path.stem
        ext = input_path.suffix

        if output_format and output_format != "original":
            ext = f".{output_format.lstrip('.').lower()}"

        # Construct clear suffix tag (e.g., _2x_16-9)
        ratio_tag = aspect_ratio.id.replace(":", "-")
        suffix = f"_{scale.id}_{ratio_tag}"
        filename = f"{stem}{suffix}{ext}"
        candidate = output_dir / filename

        if overwrite or not candidate.exists():
            return candidate

        # Disambiguate if collision
        counter = 1
        while candidate.exists():
            candidate = output_dir / f"{stem}{suffix}_{counter}{ext}"
            counter += 1

        return candidate

    def process_image(
        self,
        input_path: Path,
        options: ProcessingOptions,
    ) -> ProcessResult:
        """Executes full transformation pipeline for a single image."""
        start_time = time.perf_counter()

        if not input_path.is_file():
            return ProcessResult(
                input_path=input_path,
                output_path=None,
                success=False,
                execution_time_seconds=0.0,
                error_message=f"Input file does not exist: {input_path}",
            )

        try:
            # 1. Probe input dimensions
            orig_w, orig_h = self.get_image_dimensions(input_path)

            # 2. Determine output file path
            output_path = self.determine_output_path(
                input_path=input_path,
                output_dir=options.output_dir,
                scale=options.scale,
                aspect_ratio=options.aspect_ratio,
                output_format=options.output_format,
                overwrite=options.overwrite_existing,
            )

            # 3. Build argument list
            cmd, (final_w, final_h) = self.build_command(
                input_path=input_path,
                output_path=output_path,
                orig_width=orig_w,
                orig_height=orig_h,
                scale=options.scale,
                aspect_ratio=options.aspect_ratio,
                filter_opt=options.filter_option,
                output_format=options.output_format,
                jpeg_quality=options.jpeg_quality,
            )

            # Ensure parent output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 4. Execute via safe subprocess (list arguments -> no shell interpolation)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120.0,
                **self._get_subprocess_extra_kwargs(),
            )

            elapsed = time.perf_counter() - start_time
            return ProcessResult(
                input_path=input_path,
                output_path=output_path,
                success=True,
                original_size=(orig_w, orig_h),
                final_size=(final_w, final_h),
                execution_time_seconds=elapsed,
                command_executed=cmd,
            )

        except subprocess.CalledProcessError as exc:
            elapsed = time.perf_counter() - start_time
            err_msg = exc.stderr.strip() if exc.stderr else f"Exit code {exc.returncode}"
            return ProcessResult(
                input_path=input_path,
                output_path=None,
                success=False,
                execution_time_seconds=elapsed,
                error_message=f"ImageMagick processing error: {err_msg}",
            )
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            return ProcessResult(
                input_path=input_path,
                output_path=None,
                success=False,
                execution_time_seconds=elapsed,
                error_message=str(exc),
            )
