"""Application Entry Point for macOS Batch Image Resizer & Upscaler."""

import os
from pathlib import Path
import sys

# Ensure src/ is on Python search path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ui.app_window import AppWindow


def main() -> int:
    """Main application bootstrap."""
    # macOS Specific High-DPI optimizations
    if sys.platform == "darwin":
        # Enable Retina resolution rendering
        os.environ["TK_SILENCE_DEPRECATION"] = "1"

    app = AppWindow()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
