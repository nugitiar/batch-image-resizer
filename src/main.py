"""Cross-Platform Application Entry Point.

Automates batch image upscaling, aspect ratio center-cropping, and quality resampling
on macOS, Windows, and Linux.

Author: Nugi Tiartanto (@nugitiar)
Role:   Informatics Student & Software Creator
GitHub: https://github.com/nugitiar
"""

import os
from pathlib import Path
import platform
import sys

# Ensure project root is in Python sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ui.app_window import AppWindow


def configure_platform_environment() -> str:
    """Detects current operating system and applies platform-specific display optimizations.

    Returns:
        Canonical OS name: 'macOS', 'Windows', or 'Linux'
    """
    system_name = platform.system()

    if system_name == "Darwin":
        # macOS: Silence Tkinter deprecation warnings and optimize for Retina displays
        os.environ["TK_SILENCE_DEPRECATION"] = "1"
        return "macOS"

    elif system_name == "Windows":
        # Windows: Enable Per-Monitor High-DPI awareness to avoid UI blurriness
        try:
            import ctypes
            # Shcore.SetProcessDpiAwareness(1) -> PROCESS_SYSTEM_DPI_AWARE
            # Shcore.SetProcessDpiAwareness(2) -> PROCESS_PER_MONITOR_DPI_AWARE
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        return "Windows"

    elif system_name == "Linux":
        # Linux: Ensure UTF-8 locale and X11/Wayland support
        if "PYTHONIOENCODING" not in os.environ:
            os.environ["PYTHONIOENCODING"] = "utf-8"
        return "Linux"

    return system_name


def main() -> int:
    """Application bootstrap."""
    os_name = configure_platform_environment()

    app = AppWindow(os_name=os_name)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
