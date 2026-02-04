"""
notification_system.py

A lightweight toast notification system for the application.

Features:
- Toast notifications for:
    * Task failures
    * Budget warnings (when >80% of budget is spent)
    * Checkpoint saves
    * New task files detected
- Stacked in the bottom‑right corner
- Auto‑dismiss after 5 seconds
- Click to expand for more details (placeholder implementation)

The implementation is UI‑agnostic; it provides a `NotificationManager` that can be
plugged into any front‑end (Tkinter, PyQt, web UI, etc.) by registering a
renderer callback.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class Toast:
    """Represents a single toast notification."""
    title: str
    message: str
    severity: str = "info"          # info, warning, error, success
    duration: float = 5.0           # seconds before auto‑dismiss
    created_at: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    expanded: bool = False          # toggled when user clicks the toast

    def schedule_dismiss(self, dismiss_callback: Callable[[str], None]) -> None:
        """Schedule auto‑dismiss after `duration` seconds."""
        def _dismiss():
            dismiss_callback(self.id)

        timer = threading.Timer(self.duration, _dismiss)
        timer.daemon = True
        timer.start()


# --------------------------------------------------------------------------- #
# Notification manager
# --------------------------------------------------------------------------- #
class NotificationManager:
    """
    Core manager that creates and tracks toast notifications.

    UI frameworks should subscribe via `register_renderer` to receive toast
    creation / removal events.
    """

    def __init__(self):
        # Active toasts keyed by toast.id
        self._active_toasts: Dict[str, Toast] = {}
        # Renderer callback receives (event: str, toast: Toast)
        # event can be "show" or "dismiss"
        self._renderer: Optional[Callable[[str, Toast], None]] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------- #
    # Renderer registration
    # ------------------------------------------------------------------- #
    def register_renderer(self, renderer: Callable[[str, Toast], None]) -> None:
        """
        Register a UI renderer.

        The renderer will be called with:
            event: "show" | "dismiss"
            toast: the Toast instance (for "show") or a minimal Toast with only id (for "dismiss")
        """
        self._renderer = renderer

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    def _emit(self, event: str, toast: Toast) -> None:
        if self._renderer:
            try:
                self._renderer(event, toast)
            except Exception as e:
                # In production you might log this; we keep it silent here.
                pass

    def _add_toast(self, toast: Toast) -> None:
        with self._lock:
            self._active_toasts[toast.id] = toast
        self._emit("show", toast)
        toast.schedule_dismiss(self.dismiss_toast)

    # ------------------------------------------------------------------- #
    # Public API – creation helpers
    # ------------------------------------------------------------------- #
    def task_failure(self, task_name: str, error_msg: str) -> None:
        """Notify that a task has failed."""
        toast = Toast(
            title=f"Task Failure: {task_name}",
            message=error_msg,
            severity="error"
        )
        self._add_toast(toast)

    def budget_warning(self, spent_percent: float) -> None:
        """Notify when budget exceeds 80%."""
        if spent_percent <= 80:
            return  # No warning needed
        toast = Toast(
            title="Budget Warning",
            message=f"Budget usage at {spent_percent:.1f}% – nearing limit.",
            severity="warning"
        )
        self._add_toast(toast)

    def checkpoint_saved(self, checkpoint_name: str) -> None:
        """Notify that a checkpoint has been saved."""
        toast = Toast(
            title="Checkpoint Saved",
            message=f"Checkpoint '{checkpoint_name}' saved successfully.",
            severity="success"
        )
        self._add_toast(toast)

    def new_task_file_detected(self, file_path: str) -> None:
        """Notify that a new task file has been detected."""
        toast = Toast(
            title="New Task File",
            message=f"Detected new task file: {file_path}",
            severity="info"
        )
        self._add_toast(toast)

    # ------------------------------------------------------------------- #
    # Dismissal
    # ------------------------------------------------------------------- #
    def dismiss_toast(self, toast_id: str) -> None:
        """Remove a toast (auto‑dismiss or manual)."""
        with self._lock:
            toast = self._active_toasts.pop(toast_id, None)
        if toast:
            # Emit a minimal toast containing only the id for UI to remove it.
            minimal = Toast(title="", message="", id=toast_id)
            self._emit("dismiss", minimal)

    # ------------------------------------------------------------------- #
    # Interaction (click to expand)
    # ------------------------------------------------------------------- #
    def toggle_expand(self, toast_id: str) -> None:
        """Toggle expanded state when user clicks a toast."""
        with self._lock:
            toast = self._active_toasts.get(toast_id)
            if toast:
                toast.expanded = not toast.expanded
                # Re‑emit a "show" event so UI can re‑render the toast.
                self._emit("show", toast)


# --------------------------------------------------------------------------- #
# Example minimal renderer for console debugging (can be replaced by GUI code)
# --------------------------------------------------------------------------- #
def _console_renderer(event: str, toast: Toast) -> None:
    if event == "show":
        print(f"[{toast.severity.upper()}] {toast.title}: {toast.message}")
    elif event == "dismiss":
        print(f"[DISMISS] Toast {toast.id} removed.")
    else:
        print(f"[UNKNOWN EVENT] {event}")

# If this module is run directly, demonstrate a quick usage example.
if __name__ == "__main__":
    manager = NotificationManager()
    manager.register_renderer(_console_renderer)

    manager.task_failure("DataImport", "File not found: data.csv")
    manager.budget_warning(85.3)
    manager.checkpoint_saved("ckpt_2026_02_04")
    manager.new_task_file_detected("/tasks/new_job.yaml")

    # Keep the script alive long enough to see auto‑dismiss.
    time.sleep(6)