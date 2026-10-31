"""ImageMagick detection engine for macOS (Apple Silicon / Intel).

Automatically locates and validates the ImageMagick binary (magick / convert)
prioritizing Homebrew on Apple Silicon (/opt/homebrew/bin/magick).
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import List, Optional, Tuple


@dataclass
class ImageMagickInfo:
    is_available: bool
    binary_path: Optional[Path] = None
    version_string: Optional[str] = None
    major_version: int = 0
    architecture: Optional[str] = None
    is_arm64: bool = False
    supported_delegates: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def is_imagemagick_7(self) -> bool:
        return self.major_version >= 7


class ImageMagickDetector:
    """Detects and inspects system ImageMagick installation on macOS."""

    # Prioritized binary paths on macOS
    CANDIDATE_PATHS: Tuple[str, ...] = (
        # Apple Silicon Homebrew (canonical arm64 location)
        "/opt/homebrew/bin/magick",
        "/opt/homebrew/bin/convert",
        # Custom user / local bin
        os.path.expanduser("~/homebrew/bin/magick"),
        os.path.expanduser("~/.homebrew/bin/magick"),
        # Intel / Rosetta 2 Homebrew
        "/usr/local/bin/magick",
        "/usr/local/bin/convert",
        # MacPorts
        "/opt/local/bin/magick",
        "/opt/local/bin/convert",
    )

    def __init__(self, override_path: Optional[str] = None):
        self._override_path = Path(override_path) if override_path else None
        self._cached_info: Optional[ImageMagickInfo] = None

    def get_info(self, force_refresh: bool = False) -> ImageMagickInfo:
        """Returns detected ImageMagick metadata, caching after first run."""
        if self._cached_info and not force_refresh:
            return self._cached_info

        binary_path = self._find_binary()
        if not binary_path:
            self._cached_info = ImageMagickInfo(
                is_available=False,
                error_message=(
                    "ImageMagick binary not found. Please install it using Homebrew:\n"
                    "brew install imagemagick"
                ),
            )
            return self._cached_info

        # Validate by executing `magick -version`
        try:
            result = subprocess.run(
                [str(binary_path), "-version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5.0,
            )
            stdout = result.stdout

            # Parse Version string
            version_match = re.search(r"ImageMagick\s+([\d\.\-]+)", stdout)
            version_str = version_match.group(1) if version_match else "Unknown"

            # Parse Major version
            major_ver = 0
            if version_match:
                try:
                    major_ver = int(version_match.group(1).split(".")[0])
                except (ValueError, IndexError):
                    major_ver = 0

            # Detect architecture from version output or platform
            is_arm = "aarch64" in stdout or "arm64" in stdout or platform.machine() == "arm64"
            arch_str = "arm64 (Apple Silicon)" if is_arm else "x86_64"

            # Parse delegates (supported image codecs: heic, webp, jpeg, png, etc.)
            delegates: List[str] = []
            delegates_match = re.search(r"Delegates\s+\(built-in\):\s*(.+)", stdout)
            if delegates_match:
                delegates = delegates_match.group(1).split()

            self._cached_info = ImageMagickInfo(
                is_available=True,
                binary_path=binary_path,
                version_string=version_str,
                major_version=major_ver,
                architecture=arch_str,
                is_arm64=is_arm,
                supported_delegates=delegates,
            )
            return self._cached_info

        except subprocess.SubprocessError as exc:
            self._cached_info = ImageMagickInfo(
                is_available=False,
                binary_path=binary_path,
                error_message=f"Failed to execute ImageMagick binary at '{binary_path}': {exc}",
            )
            return self._cached_info
        except Exception as exc:
            self._cached_info = ImageMagickInfo(
                is_available=False,
                binary_path=binary_path,
                error_message=f"Unexpected error inspecting ImageMagick: {exc}",
            )
            return self._cached_info

    def _find_binary(self) -> Optional[Path]:
        """Locates the binary using explicit paths, override, or PATH lookup."""
        if self._override_path and self._override_path.is_file() and os.access(self._override_path, os.X_OK):
            return self._override_path

        # 1. Check known candidates (Apple Silicon Homebrew first)
        for candidate in self.CANDIDATE_PATHS:
            p = Path(candidate)
            if p.is_file() and os.access(p, os.X_OK):
                return p

        # 2. Check system PATH via shutil.which
        for name in ("magick", "convert"):
            found = shutil.which(name)
            if found:
                p = Path(found)
                if p.is_file() and os.access(p, os.X_OK):
                    return p

        return None
