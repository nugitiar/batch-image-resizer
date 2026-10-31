"""Reusable CustomTkinter UI components for Windows, macOS, and Linux.

Author: Nugi Tiartanto (@nugitiar)
Role:   Informatics Student & Independent Software Developer
GitHub: https://github.com/nugitiar
"""

import datetime
from pathlib import Path
from typing import Callable, List, Optional
import customtkinter as ctk

from .dnd_handler import register_drop_target


class DropZone(ctk.CTkFrame):
    """Modern macOS drag-and-drop zone and directory picker card."""

    def __init__(
        self,
        master,
        on_paths_selected: Callable[[List[Path]], None],
        on_browse_click: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, corner_radius=12, **kwargs)
        self.on_paths_selected = on_paths_selected
        self.on_browse_click = on_browse_click

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._default_border_color = ("#D0D5DD", "#344054")
        self._hover_border_color = ("#1D70B8", "#1D70B8")

        self.configure(
            border_width=2,
            border_color=self._default_border_color,
            fg_color=("#F0F4F8", "#1E293B"),
        )

        # Inner container
        self.inner_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inner_frame.grid(row=0, column=0, padx=20, pady=24, sticky="nsew")
        self.inner_frame.grid_columnconfigure(0, weight=1)

        # Icon / Symbol
        self.icon_label = ctk.CTkLabel(
            self.inner_frame,
            text="📁 ⇪",
            font=ctk.CTkFont(size=32),
            text_color=("#475467", "#94A3B8"),
        )
        self.icon_label.grid(row=0, column=0, pady=(0, 4))

        # Title
        self.title_label = ctk.CTkLabel(
            self.inner_frame,
            text="Drag & Drop Folder or Images Here",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.title_label.grid(row=1, column=0, pady=(0, 2))

        # Subtitle / Click to browse
        self.subtitle_label = ctk.CTkLabel(
            self.inner_frame,
            text="or click to browse your Mac's files...",
            font=ctk.CTkFont(size=12),
            text_color=("#667085", "#94A3B8"),
        )
        self.subtitle_label.grid(row=2, column=0, pady=(0, 8))

        # Current Selection Pill
        self.selection_label = ctk.CTkLabel(
            self.inner_frame,
            text="No folder selected",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=("#8F9BB3", "#64748B"),
        )
        self.selection_label.grid(row=3, column=0)

        # Make entire card clickable
        for widget in (self, self.inner_frame, self.icon_label, self.title_label, self.subtitle_label, self.selection_label):
            widget.bind("<Button-1>", lambda e: self.on_browse_click())

        # Register Drag & Drop
        self._setup_dnd()

    def _setup_dnd(self) -> None:
        def on_enter():
            self.configure(border_color=self._hover_border_color)

        def on_leave():
            self.configure(border_color=self._default_border_color)

        def on_drop(paths: List[Path]):
            self.configure(border_color=self._default_border_color)
            self.on_paths_selected(paths)

        register_drop_target(self, on_drop, on_drag_enter=on_enter, on_drag_leave=on_leave)

    def set_selection_text(self, text: str, is_active: bool = True) -> None:
        color = ("#0F172A", "#F8FAFC") if is_active else ("#8F9BB3", "#64748B")
        self.selection_label.configure(text=text, text_color=color)


class StatBadge(ctk.CTkFrame):
    """Compact summary statistic pill."""

    def __init__(self, master, label: str, value: str = "0", text_color=None, **kwargs):
        super().__init__(master, corner_radius=8, **kwargs)
        self.configure(fg_color=("#E2E8F0", "#1E293B"))

        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=ctk.CTkFont(size=11),
            text_color=("#64748B", "#94A3B8"),
        )
        self.label.pack(side="left", padx=(10, 4), pady=4)

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=text_color or ("#0F172A", "#F8FAFC"),
        )
        self.value_label.pack(side="left", padx=(0, 10), pady=4)

    def update_value(self, val: str) -> None:
        self.value_label.configure(text=val)


class LogViewer(ctk.CTkFrame):
    """Scrollable, timestamped activity log view with filtering and export."""

    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=10, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header controls
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=12, pady=(8, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Execution Log",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        clear_btn = ctk.CTkButton(
            header,
            text="Clear",
            width=55,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color=("transparent"),
            border_width=1,
            border_color=("#CBD5E1", "#475569"),
            text_color=("#475569", "#CBD5E1"),
            command=self.clear,
        )
        clear_btn.grid(row=0, column=1, padx=(0, 6))

        # Textbox
        self.textbox = ctk.CTkTextbox(
            self,
            corner_radius=8,
            font=ctk.CTkFont(family="Menlo", size=11),
            wrap="none",
        )
        self.textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.textbox.configure(state="disabled")

    def append_log(self, level: str, message: str) -> None:
        """Appends formatted message with timestamp."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] [{level.upper():<7}]"
        line = f"{prefix} {message}\n"

        self.textbox.configure(state="normal")
        self.textbox.insert("end", line)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
