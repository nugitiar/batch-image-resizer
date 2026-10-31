"""Cross-Platform ImageMagick Detection Engine (macOS, Windows, Linux).

Automatically locates and validates the ImageMagick binary ('magick', 'magick.exe', or 'convert')
with platform-specific search paths and non-intrusive subprocess execution.

Author: Nugi Tiartanto (@nugitiar)
"""

from dataclasses import dataclass, field
import glob
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
    os_name: str = "Unknown"
    is_arm64: bool = False
    supported_delegates: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def is_imagemagick_7(self) -> bool:
        return self.major_version >= 7


class ImageMagickDetector:
    """Detects and inspects system ImageMagick installation across macOS, Windows, and Linux."""

    def __init__(self, override_path: Optional[str] = None):
        self._override_path = Path(override_path) if override_path else None
        self._cached_info: Optional[ImageMagickInfo] = None
        self.system = platform.system()  # 'Darwin', 'Windows', 'Linux'

    def get_info(self, force_refresh: bool = False) -> ImageMagickInfo:
        """Returns detected ImageMagick metadata, caching after first run."""
        if self._cached_info and not force_refresh:
            return self._cached_info

        binary_path = self._find_binary()
        if not binary_path:
            install_hint = self._get_install_hint()
            self._cached_info = ImageMagickInfo(
                is_available=False,
                os_name=self._get_canonical_os_name(),
                error_message=(
                    f"ImageMagick binary not found on {self._get_canonical_os_name()}.\n\n"
                    f"{install_hint}"
                ),
            )
            return self._cached_info

        # Validate by executing `magick -version`
        try:
            # Prevent console window flash on Windows
            extra_kwargs = {}
            if self.system == "Windows":
                extra_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            result = subprocess.run(
                [str(binary_path), "-version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=8.0,
                **extra_kwargs,
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

            # Architecture detection
            mach = platform.machine().lower()
            is_arm = "arm64" in mach or "aarch64" in mach or "aarch64" in stdout or "arm64" in stdout
            if self.system == "Darwin":
                arch_str = "Apple Silicon (arm64)" if is_arm else "Intel (x86_64)"
            elif self.system == "Windows":
                arch_str = "Windows ARM64" if is_arm else "Windows x64"
            else:
                arch_str = f"Linux {mach}"

            # Parse delegates (codecs: jpeg, png, webp, heic, tiff, etc.)
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
                os_name=self._get_canonical_os_name(),
                is_arm64=is_arm,
                supported_delegates=delegates,
            )
            return self._cached_info

        except subprocess.SubprocessError as exc:
            self._cached_info = ImageMagickInfo(
                is_available=False,
                binary_path=binary_path,
                os_name=self._get_canonical_os_name(),
                error_message=f"Failed to execute ImageMagick binary at '{binary_path}': {exc}",
            )
            return self._cached_info
        except Exception as exc:
            self._cached_info = ImageMagickInfo(
                is_available=False,
                binary_path=binary_path,
                os_name=self._get_canonical_os_name(),
                error_message=f"Unexpected error inspecting ImageMagick: {exc}",
            )
            return self._cached_info

    def _find_binary(self) -> Optional[Path]:
        """Locates the binary using platform-specific candidate paths or PATH lookup."""
        if self._override_path and self._override_path.is_file() and os.access(self._override_path, os.X_OK):
            return self._override_path

        # 1. System PATH lookup via shutil.which (highest portability)
        target_names = ["magick", "magick.exe", "convert", "convert.exe"]
        for name in target_names:
            found = shutil.which(name)
            if found:
                p = Path(found)
                # On Windows, skip system convert.exe (FAT->NTFS utility)
                if self.system == "Windows" and "system32" in str(p).lower() and p.name.lower() == "convert.exe":
                    continue
                if p.is_file() and (self.system == "Windows" or os.access(p, os.X_OK)):
                    return p

        # 2. Platform-specific known candidate paths
        candidates = self._get_platform_candidates()
        for candidate in candidates:
            p = Path(candidate)
            if p.is_file() and (self.system == "Windows" or os.access(p, os.X_OK)):
                return p

        return None

    def _get_platform_candidates(self) -> List[str]:
        """Returns prioritized candidate paths tailored to the host OS."""
        candidates: List[str] = []

        if self.system == "Darwin":
            candidates.extend([
                # Apple Silicon Homebrew
                "/opt/homebrew/bin/magick",
                "/opt/homebrew/bin/convert",
                # Intel Homebrew
                "/usr/local/bin/magick",
                "/usr/local/bin/convert",
                # MacPorts
                "/opt/local/bin/magick",
                "/opt/local/bin/convert",
            ])

        elif self.system == "Windows":
            # Search common Windows Program Files installation directories
            for pf_env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
                base = os.environ.get(pf_env)
                if base:
                    matches = glob.glob(os.path.join(base, "ImageMagick*", "magick.exe"))
                    candidates.extend(matches)
            # Chocolatey or scoop paths
            candidates.extend([
                r"C:\Program Files\ImageMagick-7\magick.exe",
                r"C:\ProgramData\chocolatey\bin\magick.exe",
                os.path.expanduser(r"~\scoop\apps\imagemagick\current\magick.exe"),
            ])

        elif self.system == "Linux":
            candidates.extend([
                "/usr/bin/magick",
                "/usr/local/bin/magick",
                "/usr/bin/convert",
                "/usr/local/bin/convert",
                "/snap/bin/imagemagick",
            ])

        return candidates

    def _get_canonical_os_name(self) -> str:
        if self.system == "Darwin":
            return "macOS"
        elif self.system == "Windows":
            return "Windows"
        elif self.system == "Linux":
            return "Linux"
        return self.system

    def _get_install_hint(self) -> str:
        """Returns helpful installation commands tailored to current OS."""
        if self.system == "Darwin":
            return "Install via Homebrew: brew install imagemagick"
        elif self.system == "Windows":
            return (
                "Install via Windows Package Manager: winget install ImageMagick.ImageMagick\n"
                "or download the installer from: https://imagemagick.org/script/download.php"
            )
        elif self.system == "Linux":
            return (
                "Install via your package manager:\n"
                "  Debian/Ubuntu: sudo apt install imagemagick\n"
                "  Arch Linux:    sudo pacman -S imagemagick\n"
                "  Fedora:        sudo dnf install ImageMagick"
            )
        return "Please install ImageMagick 7 from https://imagemagick.org"
