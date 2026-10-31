"""Threaded batch worker engine for concurrent image processing.

Provides non-blocking execution using concurrent.futures.ThreadPoolExecutor,
safe cancellation, and granular real-time event callbacks for the UI.
"""

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import os
from pathlib import Path
import threading
import time
from typing import Callable, List, Optional

from .config import ProcessingOptions, ProcessResult
from .processor import ImageProcessor


@dataclass
class BatchSummary:
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    cancelled: bool = False
    total_duration_seconds: float = 0.0
    failed_results: List[ProcessResult] = field(default_factory=list)

    @property
    def avg_seconds_per_image(self) -> float:
        processed = self.successful + self.failed
        return (self.total_duration_seconds / processed) if processed > 0 else 0.0


class BatchWorker:
    """Manages concurrent execution of image resizing batch jobs."""

    def __init__(
        self,
        processor: ImageProcessor,
        options: ProcessingOptions,
        on_batch_start: Optional[Callable[[int], None]] = None,
        on_file_start: Optional[Callable[[int, int, Path], None]] = None,
        on_file_complete: Optional[Callable[[int, int, ProcessResult], None]] = None,
        on_log: Optional[Callable[[str, str], None]] = None,
        on_batch_finish: Optional[Callable[[BatchSummary], None]] = None,
    ):
        self.processor = processor
        self.options = options
        self.on_batch_start = on_batch_start
        self.on_file_start = on_file_start
        self.on_file_complete = on_file_complete
        self.on_log = on_log
        self.on_batch_finish = on_batch_finish

        self._cancel_event = threading.Event()
        self._is_running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        """Starts batch processing in a dedicated background worker thread."""
        if self._is_running:
            return

        self._cancel_event.clear()
        self._is_running = True
        self._worker_thread = threading.Thread(
            target=self._run_batch,
            name="BatchWorkerThread",
            daemon=True,
        )
        self._worker_thread.start()

    def cancel(self) -> None:
        """Requests immediate cancellation of pending and active batch tasks."""
        self._cancel_event.set()
        if self.on_log:
            self.on_log("WARNING", "Cancellation requested. Finishing in-flight tasks...")

    def _run_batch(self) -> None:
        """Internal execution loop using ThreadPoolExecutor."""
        start_time = time.perf_counter()
        files = self.options.input_paths
        total_files = len(files)

        summary = BatchSummary(total_files=total_files)

        if self.on_batch_start:
            self.on_batch_start(total_files)

        if self.on_log:
            self.on_log(
                "INFO",
                f"Starting batch job: {total_files} images with {self.options.concurrency} concurrent workers.",
            )

        completed_count = 0

        # Optimal worker count for Apple Silicon
        max_workers = max(1, self.options.concurrency)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map future -> input_path
            futures_map: dict[Future[ProcessResult], Path] = {}

            for file_path in files:
                if self._cancel_event.is_set():
                    summary.cancelled = True
                    break

                future = executor.submit(self._process_single, file_path)
                futures_map[future] = file_path

            # Collect completed futures as they finish
            for future in as_completed(futures_map):
                if self._cancel_event.is_set() and not summary.cancelled:
                    summary.cancelled = True

                try:
                    result = future.result()
                except Exception as exc:
                    file_path = futures_map[future]
                    result = ProcessResult(
                        input_path=file_path,
                        output_path=None,
                        success=False,
                        error_message=f"Unhandled worker exception: {exc}",
                    )

                with self._lock:
                    completed_count += 1
                    if result.success:
                        summary.successful += 1
                    else:
                        summary.failed += 1
                        summary.failed_results.append(result)

                if self.on_file_complete:
                    self.on_file_complete(completed_count, total_files, result)

        summary.total_duration_seconds = time.perf_counter() - start_time
        self._is_running = False

        if self.on_batch_finish:
            self.on_batch_finish(summary)

    def _process_single(self, file_path: Path) -> ProcessResult:
        """Processes an individual image, respecting the cancel signal."""
        if self._cancel_event.is_set():
            return ProcessResult(
                input_path=file_path,
                output_path=None,
                success=False,
                error_message="Skipped (Job cancelled by user)",
            )
        return self.processor.process_image(file_path, self.options)
