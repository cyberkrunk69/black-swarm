"""
notification_system.py

A lightweight toast‑style notification system for the Claude Parasite Brain Suck project.

Features
--------
- Failure notifications
- Budget warnings (when >80% of the budget is spent)
- Checkpoint save confirmations
- New task file detection alerts
- Stacked in the lower‑right corner
- Auto‑dismiss after 5 seconds
- Click to expand (opens a simple detail window)

Implementation notes
--------------------
- On Windows the `win10toast_click` library is used for native toasts with click callbacks.
- On other platforms a fallback implementation using `tkinter` is provided.
- All public helpers are thin wrappers around a singleton ``Notifier`` instance.
"""

import sys
import threading
import platform
from pathlib import Path
from typing import Callable, Optional

# --------------------------------------------------------------------------- #
# Platform‑specific toast implementation
# --------------------------------------------------------------------------- #
if platform.system() == "Windows":
    try:
        from win10toast_click import ToastNotifier  # type: ignore
    except ImportError:
        ToastNotifier = None
else:
    ToastNotifier = None

# --------------------------------------------------------------------------- #
# Helper: simple Tkinter fallback (used on non‑Windows or when win10toast is missing)
# --------------------------------------------------------------------------- #
if ToastNotifier is None:
    import tkinter as tk
    from tkinter import messagebox

    class _TkToast:
        """Very small Tkinter based toast replacement."""
        def __init__(self):
            self.root = tk.Tk()
            self.root.withdraw()  # hide main window
            self._lock = threading.Lock()

        def show_toast(self,
                       title: str,
                       msg: str,
                       duration: int = 5,
                       callback: Optional[Callable[[], None]] = None):
            """Display a toast‑like window that auto‑closes after ``duration`` seconds."""
            def _show():
                with self._lock:
                    win = tk.Toplevel()
                    win.title(title)
                    win.resizable(False, False)
                    win.attributes("-topmost", True)
                    # Position in lower‑right corner
                    win.update_idletasks()
                    screen_w = win.winfo_screenwidth()
                    screen_h = win.winfo_screenheight()
                    win.geometry(f"+{screen_w - 300}+{screen_h - 100}")

                    lbl = tk.Label(win, text=msg, justify="left", anchor="w")
                    lbl.pack(padx=10, pady=5)

                    # Click to expand
                    if callback:
                        btn = tk.Button(win, text="Details", command=lambda: (callback(), win.destroy()))
                        btn.pack(pady=(0, 5))

                    # Auto‑dismiss
                    win.after(duration * 1000, win.destroy)
                    win.mainloop()

            threading.Thread(target=_show, daemon=True).start()


# --------------------------------------------------------------------------- #
# Core Notifier class
# --------------------------------------------------------------------------- #
class Notifier:
    """Singleton that abstracts toast creation across platforms."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_backend()
            return cls._instance

    def _init_backend(self):
        if ToastNotifier:
            self.backend = ToastNotifier()
        else:
            self.backend = _TkToast()

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def toast(self,
              title: str,
              message: str,
              on_click: Optional[Callable[[], None]] = None,
              duration: int = 5):
        """
        Show a toast.

        Parameters
        ----------
        title: str
            Header of the toast.
        message: str
            Body text.
        on_click: Callable, optional
            Function called when the user clicks the toast (or the “Details” button in the fallback).
        duration: int, default 5
            Seconds before the toast disappears automatically.
        """
        if ToastNotifier:
            # win10toast_click supports a callback for click events
            self.backend.show_toast(
                title,
                message,
                duration=duration,
                threaded=True,
                callback_on_click=on_click if on_click else lambda: None,
                icon_path=None,
            )
        else:
            self.backend.show_toast(title, message, duration=duration, callback=on_click)


# --------------------------------------------------------------------------- #
# Convenience wrapper functions (used throughout the code base)
# --------------------------------------------------------------------------- #
_notifier = Notifier()


def notify_failure(task_name: str, error_msg: str):
    """Toast for a task that has failed."""
    title = "Task Failure"
    body = f"Task '{task_name}' failed:\n{error_msg}"
    _notifier.toast(title, body)


def notify_budget_warning(percent_used: float, budget_limit: float = 80.0):
    """Toast when budget usage exceeds the warning threshold."""
    title = "Budget Warning"
    body = f"Budget usage at {percent_used:.1f}% (threshold {budget_limit}%)."
    _notifier.toast(title, body)


def notify_checkpoint(save_name: str, save_path: Path):
    """Toast confirming that a checkpoint has been saved."""
    title = "Checkpoint Saved"
    body = f"'{save_name}' saved to {save_path}"
    _notifier.toast(title, body)


def notify_new_task_file(file_path: Path):
    """Toast for detection of a new task file."""
    title = "New Task File Detected"
    body = f"New task file found: {file_path.name}"
    _notifier.toast(title, body)


# --------------------------------------------------------------------------- #
# Optional: detailed view for expanded notifications
# --------------------------------------------------------------------------- #
def _show_detail_window(title: str, detail: str):
    """Fallback detail window for the Tkinter implementation."""
    def _run():
        root = tk.Tk()
        root.title(title)
        txt = tk.Text(root, wrap="word", width=60, height=20)
        txt.insert("1.0", detail)
        txt.config(state="disabled")
        txt.pack(expand=True, fill="both")
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()


# Example usage (can be removed in production)
if __name__ == "__main__":
    # Demo each notification type
    notify_failure("DataImport", "File not found.")
    notify_budget_warning(85.3)
    notify_checkpoint("epoch_10", Path("checkpoints/epoch_10.ckpt"))
    notify_new_task_file(Path("tasks/new_task.yaml"))