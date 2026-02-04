"""
notification_system.py

A lightweight, framework‑agnostic toast‑style notification system.

Features
--------
* Toast notifications appear in the corner of the UI.
* Auto‑dismiss after 5 seconds.
* Click (or programmatic) to expand for more details.
* Pre‑defined helpers for common events:
    - Task failure
    - Budget warning (>80% spent)
    - Checkpoint save
    - New task file detection
"""

import threading
import time
import uuid
from collections import deque
from typing import Callable, Optional

# --------------------------------------------------------------------------- #
# Core toast implementation (console‑based placeholder)
# --------------------------------------------------------------------------- #
class Toast:
    """
    Represents a single toast notification.

    In a real UI this would create a small popup in the corner.
    Here we simulate it with console output and timers.
    """

    _active_toasts: deque = deque()  # track currently displayed toasts

    def __init__(
        self,
        title: str,
        message: str,
        on_click: Optional[Callable[["Toast"], None]] = None,
        auto_dismiss: float = 5.0,
    ):
        self.id = uuid.uuid4()
        self.title = title
        self.message = message
        self.on_click = on_click
        self.auto_dismiss = auto_dismiss
        self._dismissed = False
        self._expanded = False

    def _display(self):
        """Render the toast (placeholder)."""
        Toast._active_toasts.append(self)
        print(f"[TOAST] {self.title}: {self.message} (id={self.id})")

    def _clear(self):
        """Remove the toast from display."""
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
        print(f"[TOAST DISMISSED] {self.title} (id={self.id})")
        self._dismissed = True

    def show(self):
        """Public entry point – display and schedule auto‑dismiss."""
        self._display()
        if self.auto_dismiss > 0:
            threading.Timer(self.auto_dismiss, self.dismiss).start()

    def dismiss(self):
        """Dismiss the toast (idempotent)."""
        if not self._dismissed:
            self._clear()

    def click(self):
        """Simulate a user click – expands and calls the callback."""
        if self._dismissed:
            return
        self._expanded = True
        print(f"[TOAST CLICKED] {self.title} (id={self.id}) – expanding...")
        if self.on_click:
            try:
                self.on_click(self)
            except Exception as exc:
                print(f"[TOAST ERROR] Click handler raised: {exc}")

    # ----------------------------------------------------------------------- #
    # Convenience factory methods for common notification types
    # ----------------------------------------------------------------------- #
    @staticmethod
    def failure(task_name: str, error_msg: str) -> "Toast":
        title = "Task Failure"
        message = f"Task '{task_name}' failed: {error_msg}"
        return Toast(title, message)

    @staticmethod
    def budget_warning(percent_used: float) -> "Toast":
        title = "Budget Warning"
        message = f"Budget usage at {percent_used:.1f}% (threshold >80%)."
        return Toast(title, message)

    @staticmethod
    def checkpoint_saved(checkpoint_name: str) -> "Toast":
        title = "Checkpoint Saved"
        message = f"Checkpoint '{checkpoint_name}' saved successfully."
        return Toast(title, message)

    @staticmethod
    def new_task_file(file_path: str) -> "Toast":
        title = "New Task File Detected"
        message = f"New task file discovered: {file_path}"
        return Toast(title, message)


# --------------------------------------------------------------------------- #
# Helper functions that the rest of the application can import
# --------------------------------------------------------------------------- #
def notify_task_failure(task_name: str, error_msg: str):
    """Show a toast for a failed task."""
    toast = Toast.failure(task_name, error_msg)
    toast.show()


def notify_budget_warning(percent_used: float):
    """Show a toast when budget exceeds 80%."""
    if percent_used > 80.0:
        toast = Toast.budget_warning(percent_used)
        toast.show()


def notify_checkpoint_save(checkpoint_name: str):
    """Show a toast when a checkpoint is saved."""
    toast = Toast.checkpoint_saved(checkpoint_name)
    toast.show()


def notify_new_task_file(file_path: str):
    """Show a toast when a new task file appears."""
    toast = Toast.new_task_file(file_path)
    toast.show()


# --------------------------------------------------------------------------- #
# Example usage (remove or guard under __main__ in production)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simulate a series of notifications
    notify_task_failure("DataImport", "File not found")
    notify_budget_warning(85.3)
    notify_checkpoint_save("epoch_12")
    notify_new_task_file("/data/tasks/new_job.yaml")

    # Keep the main thread alive long enough for auto‑dismiss timers
    time.sleep(6)