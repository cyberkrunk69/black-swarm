"""
notification_system.py

A lightweight toast‑style notification system for the application.
It supports four notification types:

* Task failure
* Budget warning (when >80% of the budget is spent)
* Checkpoint saved
* New task file detected

Features
--------
* Stacked in the bottom‑right corner of the screen.
* Auto‑dismiss after 5 seconds.
* Click to expand (show full message until manually closed).

Implementation notes
--------------------
* Uses ``tkinter`` – a standard library GUI toolkit – to avoid external
  dependencies.
* ``NotificationManager`` is a singleton‑style class; import it and call the
  class methods to emit notifications from anywhere in the code base.
* The manager keeps track of active toasts to position new ones above the
  previous ones.
"""

import tkinter as tk
import threading
import time
from typing import Callable, List

# --------------------------------------------------------------------------- #
# Helper: run tkinter mainloop in a dedicated daemon thread
# --------------------------------------------------------------------------- #
class _TkThread(threading.Thread):
    """Singleton thread that runs a hidden Tk root."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(_TkThread, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        super().__init__(daemon=True)
        self.root = tk.Tk()
        self.root.withdraw()          # hide the main window
        self.root.after(0, lambda: None)  # kick the event loop
        self._initialized = True
        self.start()

    def run(self):
        self.root.mainloop()


# --------------------------------------------------------------------------- #
# Toast widget
# --------------------------------------------------------------------------- #
class _Toast(tk.Toplevel):
    """A single toast notification."""

    WIDTH = 300
    HEIGHT = 80
    PADDING = 10
    AUTO_DISMISS_MS = 5000

    def __init__(self, master, title: str, message: str, on_close: Callable):
        super().__init__(master)
        self.title(title)
        self.overrideredirect(True)          # no window decorations
        self.configure(background="#333333")
        self.resizable(False, False)

        # Store callback
        self._on_close = on_close

        # Layout
        self._title_label = tk.Label(
            self,
            text=title,
            font=("Helvetica", 10, "bold"),
            fg="white",
            bg="#333333",
        )
        self._title_label.pack(fill="x", padx=8, pady=(6, 0))

        self._msg_label = tk.Label(
            self,
            text=message,
            font=("Helvetica", 9),
            fg="white",
            bg="#333333",
            wraplength=self.WIDTH - 20,
            justify="left",
        )
        self._msg_label.pack(fill="both", expand=True, padx=8, pady=4)

        # Bind click to expand/collapse
        self._expanded = False
        self.bind("<Button-1>", self._toggle_expand)
        self._title_label.bind("<Button-1>", self._toggle_expand)
        self._msg_label.bind("<Button-1>", self._toggle_expand)

        # Auto‑dismiss timer
        self.after(self.AUTO_DISMISS_MS, self._close)

    def _toggle_expand(self, event=None):
        """Toggle between compact and expanded view."""
        if self._expanded:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        else:
            # Expand to fit full message (max 300px height)
            self.update_idletasks()
            req_h = self._msg_label.winfo_reqheight() + 30
            new_h = min(req_h, 300)
            self.geometry(f"{self.WIDTH}x{new_h}")
        self._expanded = not self._expanded

    def _close(self):
        """Close the toast and notify the manager."""
        self.destroy()
        if self._on_close:
            self._on_close(self)


# --------------------------------------------------------------------------- #
# Notification manager
# --------------------------------------------------------------------------- #
class NotificationManager:
    """Singleton manager handling toast creation and stacking."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(NotificationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        # Ensure Tk thread is running
        self._tk_thread = _TkThread()
        self._root = self._tk_thread.root
        self._active_toasts: List[_Toast] = []
        self._initialized = True

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    @staticmethod
    def _format_message(title: str, body: str) -> (str, str):
        """Utility to keep title/body handling consistent."""
        return title, body

    def _show_toast(self, title: str, message: str):
        """Create and display a toast, handling stacking."""
        # Create toast on the Tk thread via `after`
        def _create():
            toast = _Toast(
                master=self._root,
                title=title,
                message=message,
                on_close=self._remove_toast,
            )
            # Position toast
            self._position_toast(toast)
            self._active_toasts.append(toast)

        self._root.after(0, _create)

    def _position_toast(self, toast: _Toast):
        """Place toast at bottom‑right, stacked upwards."""
        self._root.update_idletasks()
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()

        # Calculate offset based on existing toasts
        offset_y = sum(t.winfo_height() + _Toast.PADDING for t in self._active_toasts)
        x = screen_w - _Toast.WIDTH - _Toast.PADDING
        y = screen_h - offset_y - _Toast.HEIGHT - _Toast.PADDING

        toast.geometry(f"{_Toast.WIDTH}x{_Toast.HEIGHT}+{x}+{y}")

    def _remove_toast(self, toast: _Toast):
        """Called when a toast is destroyed – update stack."""
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
            # Re‑position remaining toasts
            for t in self._active_toasts:
                self._position_toast(t)

    # --------------------------------------------------------------------- #
    # Specific notification helpers
    # --------------------------------------------------------------------- #
    def notify_task_failure(self, task_name: str, error_msg: str):
        title, body = self._format_message(
            "Task Failure",
            f"Task '{task_name}' failed.\nError: {error_msg}",
        )
        self._show_toast(title, body)

    def notify_budget_warning(self, percent_used: float, limit: float = 80.0):
        title, body = self._format_message(
            "Budget Warning",
            f"Budget usage at {percent_used:.1f}% (warning threshold: {limit}%).",
        )
        self._show_toast(title, body)

    def notify_checkpoint_saved(self, checkpoint_id: str, path: str):
        title, body = self._format_message(
            "Checkpoint Saved",
            f"Checkpoint '{checkpoint_id}' saved to:\n{path}",
        )
        self._show_toast(title, body)

    def notify_new_task_file(self, file_path: str):
        title, body = self._format_message(
            "New Task File Detected",
            f"A new task file was found:\n{file_path}",
        )
        self._show_toast(title, body)


# --------------------------------------------------------------------------- #
# Convenience singleton instance
# --------------------------------------------------------------------------- #
notification_manager = NotificationManager()

# --------------------------------------------------------------------------- #
# Example usage (remove or comment out in production)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple demo showing all four types
    nm = notification_manager
    nm.notify_task_failure("DataImport", "File not found")
    nm.notify_budget_warning(85.2)
    nm.notify_checkpoint_saved("ckpt_2026_02_04", "/tmp/checkpoints/ckpt_01.bin")
    nm.notify_new_task_file("/app/tasks/new_task.yaml")
    # Keep the script alive long enough to see toasts
    time.sleep(7)