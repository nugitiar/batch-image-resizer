"""Drag-and-Drop integration for CustomTkinter on macOS.

Integrates tkinterdnd2 with CustomTkinter windows with robust fallback
if native TkinterDnD tcl libraries are unavailable on the system.
"""

from pathlib import Path
import re
from typing import Callable, List, Optional
import urllib.parse


def parse_dropped_paths(raw_data: str) -> List[Path]:
    """Parses raw drag-and-drop string into normalized Path objects.

    Handles:
    - Curly brace quoted paths from TkinterDnD: {/Path With Spaces/file.png}
    - file:// URL scheme strings
    - Space-separated unquoted paths
    """
    paths: List[Path] = []
    if not raw_data:
        return paths

    # Pattern for {paths with spaces} or single_unspaced_tokens
    pattern = r"\{([^}]+)\}|(\S+)"
    matches = re.findall(pattern, raw_data.strip())

    for braced, unbraced in matches:
        token = (braced or unbraced).strip()
        if not token:
            continue

        # Convert file:// URL scheme if present
        if token.startswith("file://"):
            token = urllib.parse.unquote(urllib.parse.urlparse(token).path)

        p = Path(token).expanduser().resolve()
        if p.exists():
            paths.append(p)

    return paths


# Check if TkinterDnD is available in the environment
HAS_TKINTERDND = False
TkinterDnD_Class = object
DND_FILES_EVENT = "DND_Files"

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_TKINTERDND = True
    TkinterDnD_Class = TkinterDnD.DnDWrapper
    DND_FILES_EVENT = DND_FILES
except ImportError:
    HAS_TKINTERDND = False


def register_drop_target(
    widget,
    callback: Callable[[List[Path]], None],
    on_drag_enter: Optional[Callable[[], None]] = None,
    on_drag_leave: Optional[Callable[[], None]] = None,
) -> bool:
    """Safely registers drag-and-drop handler onto a CustomTkinter widget.

    Returns True if successfully registered, False if TkinterDnD is unavailable.
    """
    if not HAS_TKINTERDND:
        return False

    try:
        # Register drop target on widget's underlying Tkinter instance
        target = getattr(widget, "_canvas", widget)

        def _on_drop(event):
            raw = getattr(event, "data", "")
            parsed = parse_dropped_paths(raw)
            if parsed:
                callback(parsed)
            if on_drag_leave:
                on_drag_leave()

        def _on_enter(event):
            if on_drag_enter:
                on_drag_enter()

        def _on_leave(event):
            if on_drag_leave:
                on_drag_leave()

        target.drop_target_register(DND_FILES_EVENT)
        target.dnd_bind("<<Drop>>", _on_drop)
        target.dnd_bind("<<DragEnter>>", _on_enter)
        target.dnd_bind("<<DragLeave>>", _on_leave)
        return True

    except Exception:
        # Gracefully handle environment where TkinterDnD tcl extension fails to load
        return False
