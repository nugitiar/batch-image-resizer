"""Main Application Window built with CustomTkinter.

Provides native macOS aesthetic, dark/light mode toggle, drag-and-drop input,
parameter controls (2x/3x/4x, aspect ratios, Lanczos/Cubic filters),
real-time progress feedback, thread-safe asynchronous execution, and logging.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import time
from typing import List, Optional, Set
import customtkinter as ctk
from tkinter import filedialog, messagebox

from ..core.config import (
    ASPECT_RATIOS,
    RESIZE_FILTERS,
    SCALE_MULTIPLIERS,
    SUPPORTED_EXTENSIONS,
    AspectRatioOption,
    FilterOption,
    ProcessingOptions,
    ProcessResult,
    ScaleOption,
)
from ..core.detector import ImageMagickDetector, ImageMagickInfo
from ..core.processor import ImageProcessor
from ..core.worker import BatchSummary, BatchWorker
from .components import DropZone, LogViewer, StatBadge
from .dnd_handler import HAS_TKINTERDND, TkinterDnD_Class


# Set default appearance to match macOS system preference
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class AppWindow(ctk.CTk, TkinterDnD_Class if HAS_TKINTERDND else object):
    """The primary desktop GUI window for macOS Batch Image Resizer."""

    def __init__(self):
        super().__init__()

        # Try initializing TkinterDnD backend if available
        if HAS_TKINTERDND:
            try:
                from tkinterdnd2 import TkinterDnD
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception:
                pass

        # Window Configuration
        self.title("Batch Image Upscaler & Resizer — macOS Apple Silicon")
        self.geometry("1060x820")
        self.minsize(940, 720)

        # State Variables
        self.detector = ImageMagickDetector()
        self.im_info: ImageMagickInfo = self.detector.get_info()
        self.processor: Optional[ImageProcessor] = None
        if self.im_info.is_available:
            self.processor = ImageProcessor(self.im_info)

        self.input_files: List[Path] = []
        self.input_dir: Optional[Path] = None
        self.output_dir: Optional[Path] = None
        self.current_worker: Optional[BatchWorker] = None
        self.batch_start_timestamp: float = 0.0

        # UI Layout Construction
        self._build_ui()
        self._update_magick_status_badge()

    def _build_ui(self) -> None:
        """Constructs modern macOS interface with responsive layout."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # Log viewer expands

        # ======================================================================
        # 1. Top Header Bar (Title, ImageMagick Status, Dark/Light Mode)
        # ======================================================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(16, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        # App Title & Subtitle
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        title_lbl = ctk.CTkLabel(
            title_box,
            text="Batch Image Resizer",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title_lbl.pack(anchor="w")

        subtitle_lbl = ctk.CTkLabel(
            title_box,
            text="Native Apple Silicon (arm64) • ImageMagick CLI Execution Engine",
            font=ctk.CTkFont(size=12),
            text_color=("#64748B", "#94A3B8"),
        )
        subtitle_lbl.pack(anchor="w")

        # Right-side utilities: Magick status & Theme selector
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.grid(row=0, column=1, sticky="e")

        self.magick_badge = ctk.CTkLabel(
            right_box,
            text="Checking ImageMagick...",
            font=ctk.CTkFont(family="Menlo", size=11),
            corner_radius=6,
            padx=10,
            pady=4,
        )
        self.magick_badge.pack(side="left", padx=(0, 12))

        self.theme_menu = ctk.CTkOptionMenu(
            right_box,
            values=["System", "Dark", "Light"],
            width=95,
            height=28,
            font=ctk.CTkFont(size=11),
            command=self._on_theme_change,
        )
        self.theme_menu.set("System")
        self.theme_menu.pack(side="left")

        # ======================================================================
        # 2. Main Work Area (2 Columns: Input/Output & Parameters)
        # ======================================================================
        work_area = ctk.CTkFrame(self, fg_color="transparent")
        work_area.grid(row=1, column=0, padx=24, pady=0, sticky="ew")
        work_area.grid_columnconfigure(0, weight=6)  # Left: File Management
        work_area.grid_columnconfigure(1, weight=5)  # Right: Parameters

        # ----------------------------------------------------------------------
        # Left Column: Input / Output Folders
        # ----------------------------------------------------------------------
        left_col = ctk.CTkFrame(work_area, corner_radius=12)
        left_col.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        left_col.grid_columnconfigure(0, weight=1)

        col_title1 = ctk.CTkLabel(
            left_col,
            text="1. Select Input & Output Folders",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        col_title1.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        # Drag and Drop Zone
        self.drop_zone = DropZone(
            left_col,
            on_paths_selected=self._handle_dropped_paths,
            on_browse_click=self._browse_input_folder,
        )
        self.drop_zone.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="ew")

        # Output Folder Selection Card
        out_frame = ctk.CTkFrame(left_col, fg_color=("#F0F4F8", "#1E293B"), corner_radius=8)
        out_frame.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="ew")
        out_frame.grid_columnconfigure(0, weight=1)

        out_lbl = ctk.CTkLabel(
            out_frame,
            text="Destination Folder:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        out_lbl.grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        self.out_path_label = ctk.CTkLabel(
            out_frame,
            text="Auto: <Input_Folder>_processed",
            font=ctk.CTkFont(size=12),
            text_color=("#64748B", "#94A3B8"),
            anchor="w",
        )
        self.out_path_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        out_btn_box = ctk.CTkFrame(out_frame, fg_color="transparent")
        out_btn_box.grid(row=1, column=1, padx=12, pady=(0, 10), sticky="e")

        choose_out_btn = ctk.CTkButton(
            out_btn_box,
            text="Change...",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            command=self._browse_output_folder,
        )
        choose_out_btn.pack(side="left", padx=(0, 6))

        # ----------------------------------------------------------------------
        # Right Column: Transformation Controls & Parameters
        # ----------------------------------------------------------------------
        right_col = ctk.CTkFrame(work_area, corner_radius=12)
        right_col.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        right_col.grid_columnconfigure(1, weight=1)

        col_title2 = ctk.CTkLabel(
            right_col,
            text="2. Configure Transformation Parameters",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        col_title2.grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 12), sticky="w")

        # Parameter 1: Scale Multiplier (Segmented Control)
        scale_lbl = ctk.CTkLabel(
            right_col,
            text="Scale Multiplier:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        scale_lbl.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        self.scale_seg = ctk.CTkSegmentedButton(
            right_col,
            values=["1x (None)", "2x", "3x", "4x"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.scale_seg.set("2x")
        self.scale_seg.grid(row=1, column=1, padx=(0, 16), pady=(0, 10), sticky="ew")

        # Parameter 2: Aspect Ratio (Dropdown)
        aspect_lbl = ctk.CTkLabel(
            right_col,
            text="Aspect Ratio / Crop:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        aspect_lbl.grid(row=2, column=0, padx=16, pady=(0, 10), sticky="w")

        self.aspect_menu = ctk.CTkOptionMenu(
            right_col,
            values=[opt.label for opt in ASPECT_RATIOS.values()],
            font=ctk.CTkFont(size=12),
        )
        self.aspect_menu.set(ASPECT_RATIOS["original"].label)
        self.aspect_menu.grid(row=2, column=1, padx=(0, 16), pady=(0, 10), sticky="ew")

        # Parameter 3: Resize Algorithm (Dropdown)
        filter_lbl = ctk.CTkLabel(
            right_col,
            text="Quality Algorithm:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        filter_lbl.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="w")

        self.filter_menu = ctk.CTkOptionMenu(
            right_col,
            values=[opt.label for opt in RESIZE_FILTERS.values()],
            font=ctk.CTkFont(size=12),
        )
        self.filter_menu.set(RESIZE_FILTERS["Lanczos"].label)
        self.filter_menu.grid(row=3, column=1, padx=(0, 16), pady=(0, 10), sticky="ew")

        # Parameter 4: Output Format (Dropdown)
        format_lbl = ctk.CTkLabel(
            right_col,
            text="Output Format:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        format_lbl.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="w")

        self.format_menu = ctk.CTkOptionMenu(
            right_col,
            values=["Same as Original", "PNG (Lossless)", "JPEG (Standard)", "WebP (Modern Web)"],
            font=ctk.CTkFont(size=12),
        )
        self.format_menu.set("Same as Original")
        self.format_menu.grid(row=4, column=1, padx=(0, 16), pady=(0, 10), sticky="ew")

        # Parameter 5: Apple Silicon Concurrency / CPU Cores
        cores_lbl = ctk.CTkLabel(
            right_col,
            text="Parallel Workers:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        cores_lbl.grid(row=5, column=0, padx=16, pady=(0, 14), sticky="w")

        default_workers = min(8, os.cpu_count() or 4)
        worker_options = ["2 Cores", "4 Cores", "8 Cores", "12 Cores", "16 Cores"]
        selected_worker_str = f"{default_workers} Cores"
        if selected_worker_str not in worker_options:
            worker_options.append(selected_worker_str)
            worker_options.sort(key=lambda s: int(s.split()[0]))

        self.workers_menu = ctk.CTkOptionMenu(
            right_col,
            values=worker_options,
            font=ctk.CTkFont(size=12),
        )
        self.workers_menu.set(selected_worker_str)
        self.workers_menu.grid(row=5, column=1, padx=(0, 16), pady=(0, 14), sticky="ew")

        # ======================================================================
        # 3. Actions & Live Progress Section
        # ======================================================================
        action_frame = ctk.CTkFrame(self, corner_radius=12)
        action_frame.grid(row=2, column=0, padx=24, pady=12, sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        # Top row of action card: Buttons and Badges
        act_header = ctk.CTkFrame(action_frame, fg_color="transparent")
        act_header.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="ew")
        act_header.grid_columnconfigure(3, weight=1)

        self.start_btn = ctk.CTkButton(
            act_header,
            text="▶  Start Batch Processing",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#0066CC",
            hover_color="#0052A3",
            command=self._start_batch,
        )
        self.start_btn.grid(row=0, column=0, padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            act_header,
            text="■  Cancel / Stop",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            state="disabled",
            command=self._cancel_batch,
        )
        self.cancel_btn.grid(row=0, column=1, padx=(0, 10))

        self.reveal_btn = ctk.CTkButton(
            act_header,
            text="Reveal Output in Finder",
            font=ctk.CTkFont(size=12),
            height=36,
            fg_color="transparent",
            border_width=1,
            border_color=("#CBD5E1", "#475569"),
            text_color=("#334155", "#E2E8F0"),
            command=self._reveal_in_finder,
        )
        self.reveal_btn.grid(row=0, column=2, padx=(0, 10))

        # Stat Badges (Right aligned)
        badges_box = ctk.CTkFrame(act_header, fg_color="transparent")
        badges_box.grid(row=0, column=3, sticky="e")

        self.badge_total = StatBadge(badges_box, label="Total:", value="0")
        self.badge_total.pack(side="left", padx=4)

        self.badge_success = StatBadge(badges_box, label="Success:", value="0", text_color="#16A34A")
        self.badge_success.pack(side="left", padx=4)

        self.badge_failed = StatBadge(badges_box, label="Failed:", value="0", text_color="#DC2626")
        self.badge_failed.pack(side="left", padx=4)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(action_frame, height=12)
        self.progress_bar.grid(row=1, column=0, padx=16, pady=(4, 6), sticky="ew")
        self.progress_bar.set(0.0)

        # Progress Status label
        self.progress_label = ctk.CTkLabel(
            action_frame,
            text="Ready. Select an input folder to begin.",
            font=ctk.CTkFont(size=12),
            text_color=("#64748B", "#94A3B8"),
            anchor="w",
        )
        self.progress_label.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="w")

        # ======================================================================
        # 4. Activity Log Viewer
        # ======================================================================
        self.log_viewer = LogViewer(self)
        self.log_viewer.grid(row=3, column=0, padx=24, pady=(0, 16), sticky="nsew")

    # ==========================================================================
    # Logic: Status Badge & Theme
    # ==========================================================================
    def _update_magick_status_badge(self) -> None:
        """Refreshes the top-bar ImageMagick status pill."""
        if self.im_info.is_available:
            arch = "arm64" if self.im_info.is_arm64 else "x86_64"
            self.magick_badge.configure(
                text=f"● ImageMagick {self.im_info.version_string} ({arch})",
                fg_color=("#DCFCE7", "#064E3B"),
                text_color=("#15803D", "#6EE7B7"),
            )
            self.log_viewer.append_log(
                "INFO",
                f"ImageMagick detected: {self.im_info.binary_path} [{arch}]",
            )
        else:
            self.magick_badge.configure(
                text="✗ ImageMagick Not Found",
                fg_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#B91C1C", "#FCA5A5"),
            )
            self.log_viewer.append_log(
                "ERROR",
                "ImageMagick CLI not detected. Run 'brew install imagemagick'.",
            )

    def _on_theme_change(self, choice: str) -> None:
        ctk.set_appearance_mode(choice)

    # ==========================================================================
    # Logic: File / Folder Selection & Drag-and-Drop
    # ==========================================================================
    def _browse_input_folder(self) -> None:
        """Opens native macOS folder selection dialog."""
        folder = filedialog.askdirectory(title="Select Folder Containing Images")
        if folder:
            self._scan_and_set_input_paths([Path(folder)])

    def _browse_output_folder(self) -> None:
        """Opens native macOS folder selection dialog for custom output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir = Path(folder)
            self.out_path_label.configure(
                text=str(self.output_dir),
                text_color=("#0F172A", "#F8FAFC"),
            )
            self.log_viewer.append_log("INFO", f"Custom output directory set to: {self.output_dir}")

    def _handle_dropped_paths(self, paths: List[Path]) -> None:
        """Processes files or folders dropped onto the application window."""
        self._scan_and_set_input_paths(paths)

    def _scan_and_set_input_paths(self, raw_paths: List[Path]) -> None:
        """Scans directories or files, filtering for supported image extensions."""
        collected_files: List[Path] = []
        primary_dir: Optional[Path] = None

        for p in raw_paths:
            if p.is_dir():
                if not primary_dir:
                    primary_dir = p
                # Collect supported files inside directory
                for item in sorted(p.iterdir()):
                    if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                        collected_files.append(item)
            elif p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                if not primary_dir:
                    primary_dir = p.parent
                collected_files.append(p)

        # Eliminate duplicates preserving order
        unique_files: List[Path] = []
        seen: Set[Path] = set()
        for f in collected_files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        self.input_files = unique_files
        self.input_dir = primary_dir

        if unique_files:
            folder_name = primary_dir.name if primary_dir else "Selected Images"
            count = len(unique_files)
            self.drop_zone.set_selection_text(
                f"Selected: {folder_name} ({count} supported image{'s' if count != 1 else ''})",
                is_active=True,
            )

            # Auto-assign default output directory if not manually customized
            if not self.output_dir or self.output_dir == self.input_dir:
                self.output_dir = primary_dir.parent / f"{primary_dir.name}_upscaled"
                self.out_path_label.configure(
                    text=f"{self.output_dir}",
                    text_color=("#0F172A", "#F8FAFC"),
                )

            self.badge_total.update_value(str(count))
            self.badge_success.update_value("0")
            self.badge_failed.update_value("0")
            self.progress_bar.set(0.0)
            self.progress_label.configure(text=f"Ready to process {count} images.")
            self.log_viewer.append_log(
                "INFO",
                f"Loaded {count} images from '{folder_name}'. Output folder: '{self.output_dir.name}'",
            )
        else:
            self.drop_zone.set_selection_text("No supported images found in selection.", is_active=False)
            messagebox.showwarning(
                "No Supported Images",
                f"No supported images ({', '.join(SUPPORTED_EXTENSIONS[:5])}...) were found in the selected location.",
            )

    # ==========================================================================
    # Logic: Batch Job Execution
    # ==========================================================================
    def _parse_options(self) -> Optional[ProcessingOptions]:
        """Reads selected GUI controls and compiles into ProcessingOptions."""
        if not self.input_files:
            messagebox.showerror("No Images", "Please select an input folder with images first.")
            return None

        if not self.output_dir:
            messagebox.showerror("No Output", "Please designate an output destination folder.")
            return None

        # Scale Multiplier
        scale_map = {
            "1x (None)": SCALE_MULTIPLIERS["1x"],
            "2x": SCALE_MULTIPLIERS["2x"],
            "3x": SCALE_MULTIPLIERS["3x"],
            "4x": SCALE_MULTIPLIERS["4x"],
        }
        chosen_scale = scale_map.get(self.scale_seg.get(), SCALE_MULTIPLIERS["2x"])

        # Aspect Ratio
        chosen_aspect_label = self.aspect_menu.get()
        chosen_aspect = next(
            (opt for opt in ASPECT_RATIOS.values() if opt.label == chosen_aspect_label),
            ASPECT_RATIOS["original"],
        )

        # Quality Filter
        chosen_filter_label = self.filter_menu.get()
        chosen_filter = next(
            (opt for opt in RESIZE_FILTERS.values() if opt.label == chosen_filter_label),
            RESIZE_FILTERS["Lanczos"],
        )

        # Format
        fmt_map = {
            "Same as Original": "original",
            "PNG (Lossless)": "png",
            "JPEG (Standard)": "jpg",
            "WebP (Modern Web)": "webp",
        }
        chosen_format = fmt_map.get(self.format_menu.get(), "original")

        # Concurrency
        workers_str = self.workers_menu.get().split()[0]
        try:
            concurrency = int(workers_str)
        except ValueError:
            concurrency = 4

        return ProcessingOptions(
            input_paths=self.input_files,
            output_dir=self.output_dir,
            scale=chosen_scale,
            aspect_ratio=chosen_aspect,
            filter_option=chosen_filter,
            output_format=chosen_format,
            concurrency=concurrency,
        )

    def _start_batch(self) -> None:
        """Validates settings and begins asynchronous concurrent processing."""
        if not self.im_info.is_available:
            messagebox.showerror(
                "ImageMagick Required",
                "ImageMagick is not available on this Mac.\n\n"
                "Install it via Terminal:\nbrew install imagemagick",
            )
            return

        options = self._parse_options()
        if not options:
            return

        # Prepare UI state for active run
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.badge_success.update_value("0")
        self.badge_failed.update_value("0")
        self.progress_bar.set(0.0)
        self.batch_start_timestamp = time.perf_counter()

        # Initialize Batch Worker
        self.current_worker = BatchWorker(
            processor=self.processor,
            options=options,
            on_batch_start=lambda total: self.after(0, self._ui_on_batch_start, total),
            on_file_complete=lambda idx, tot, res: self.after(0, self._ui_on_file_complete, idx, tot, res),
            on_log=lambda lvl, msg: self.after(0, self.log_viewer.append_log, lvl, msg),
            on_batch_finish=lambda summary: self.after(0, self._ui_on_batch_finish, summary),
        )

        self.current_worker.start()

    def _cancel_batch(self) -> None:
        """Requests cancellation of running batch worker."""
        if self.current_worker:
            self.cancel_btn.configure(state="disabled", text="Stopping...")
            self.current_worker.cancel()

    def _reveal_in_finder(self) -> None:
        """Opens the output directory in macOS Finder."""
        target = self.output_dir or (self.input_dir.parent if self.input_dir else None)
        if target:
            target.mkdir(parents=True, exist_ok=True)
            subprocess.run(["open", str(target)])
        else:
            messagebox.showinfo("Finder", "No active output folder selected yet.")

    # ==========================================================================
    # Thread-Safe UI Update Callbacks (Scheduled via self.after)
    # ==========================================================================
    def _ui_on_batch_start(self, total: int) -> None:
        self.progress_label.configure(text=f"Processing 0 of {total} images...")
        self.log_viewer.append_log(
            "INFO",
            f"Batch started: Scaling {self.scale_seg.get()} | "
            f"Ratio: {self.aspect_menu.get()} | Filter: {self.filter_menu.get()}",
        )

    def _ui_on_file_complete(self, index: int, total: int, result: ProcessResult) -> None:
        ratio = index / total if total > 0 else 1.0
        self.progress_bar.set(ratio)

        # Calculate Elapsed and ETA
        elapsed = time.perf_counter() - self.batch_start_timestamp
        avg_time = elapsed / index if index > 0 else 0.0
        remaining = max(0.0, (total - index) * avg_time)

        pct = int(round(ratio * 100))
        eta_str = time.strftime("%M:%S", time.gmtime(remaining))
        self.progress_label.configure(
            text=f"Processed {index}/{total} ({pct}%) • Elapsed: {int(elapsed)}s • ETA: ~{eta_str}"
        )

        if result.success:
            orig = f"{result.original_size[0]}x{result.original_size[1]}" if result.original_size else "?"
            fin = f"{result.final_size[0]}x{result.final_size[1]}" if result.final_size else "?"
            self.log_viewer.append_log(
                "SUCCESS",
                f"{result.input_path.name} ({orig} → {fin}) in {result.execution_time_seconds:.2f}s",
            )
            curr_succ = int(self.badge_success.value_label.cget("text"))
            self.badge_success.update_value(str(curr_succ + 1))
        else:
            self.log_viewer.append_log(
                "ERROR",
                f"{result.input_path.name}: {result.error_message}",
            )
            curr_fail = int(self.badge_failed.value_label.cget("text"))
            self.badge_failed.update_value(str(curr_fail + 1))

    def _ui_on_batch_finish(self, summary: BatchSummary) -> None:
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled", text="■  Cancel / Stop")
        self.progress_bar.set(1.0)

        status_text = "Cancelled by user" if summary.cancelled else "Batch completed"
        duration_str = f"{summary.total_duration_seconds:.2f}s"
        self.progress_label.configure(
            text=f"{status_text}! {summary.successful} succeeded, {summary.failed} failed in {duration_str}."
        )

        self.log_viewer.append_log(
            "INFO" if not summary.failed else "WARNING",
            f"=== {status_text.upper()}: {summary.successful}/{summary.total_files} succeeded "
            f"({summary.avg_seconds_per_image:.2f}s/img avg, total: {duration_str}) ===",
        )

        if not summary.cancelled and summary.successful > 0:
            messagebox.showinfo(
                "Batch Finished",
                f"Successfully processed {summary.successful} of {summary.total_files} images in {duration_str}!\n\n"
                f"Saved to:\n{self.output_dir}",
            )
