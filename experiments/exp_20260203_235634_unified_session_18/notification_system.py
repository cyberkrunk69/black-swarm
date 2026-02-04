"""
notification_system.py

Simple toast‑style notification system for the Claude Parasite Brain Suck project.

Features
--------
* Displays transient toast messages in the bottom‑right corner of the primary monitor.
* Auto‑dismiss after 5 seconds.
* Click on a toast to expand it into a larger, persistent window with the full message.
* Helper functions for the four required notification types:
    - task failures
    - budget warnings (>80% spent)
    - checkpoint saves
    - new task files detected
"""

import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Callable, Optional

# --------------------------------------------------------------------------- #
# Core toast implementation
# --------------------------------------------------------------------------- #

class _Toast(tk.Toplevel):
    """A single toast widget."""
    WIDTH = 300
    HEIGHT = 80
    PADDING = 10
    AUTO_DISMISS_MS = 5000

    def __init__(self, master: tk.Tk, title: str, message: str,
                 on_click: Optional[Callable[[], None]] = None):
        super().__init__(master)
        self.title(title)
        self.message = message
        self.on_click = on_click

        # Remove window decorations
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Layout
        self.configure(background="#333333")
        self.frame = ttk.Frame(self, padding=5, style="Toast.TFrame")
        self.frame.pack(fill="both", expand=True)

        self.title_lbl = ttk.Label(self.frame, text=title, style="Toast.Title.TLabel")
        self.title_lbl.pack(anchor="w")

        self.msg_lbl = ttk.Label(self.frame, text=message, style="Toast.Msg.TLabel", wraplength=self.WIDTH - 20)
        self.msg_lbl.pack(anchor="w")

        # Position in bottom‑right corner
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = screen_w - self.WIDTH - self.PADDING
        y = screen_h - self.HEIGHT - self.PADDING - (self.WIDTH + self.PADDING) * self.master.toast_count
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        # Bind click
        self.bind("<Button-1>", self._on_click)
        self.title_lbl.bind("<Button-1>", self._on_click)
        self.msg_lbl.bind("<Button-1>", self._on_click)

        # Auto‑dismiss timer
        self.after(self.AUTO_DISMISS_MS, self.destroy)

    def _on_click(self, event):
        if self.on_click:
            self.on_click()
        self.destroy()


class ToastNotifier:
    """Manages toast notifications for the application."""

    def __init__(self):
        # A hidden root window is required for Tkinter.
        self.root = tk.Tk()
        self.root.withdraw()          # Hide the main window
        self.root.toast_count = 0     # Used to stack multiple toasts
        self._setup_styles()
        # Run the Tkinter event loop in a daemon thread so it doesn't block the main program.
        self._event_thread = threading.Thread(target=self.root.mainloop, daemon=True)
        self._event_thread.start()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure("Toast.TFrame", background="#333333")
        style.configure("Toast.Title.TLabel", foreground="#FFFFFF", font=("Segoe UI", 10, "bold"), background="#333333")
        style.configure("Toast.Msg.TLabel", foreground="#DDDDDD", font=("Segoe UI", 9), background="#333333")

    def _show_toast(self, title: str, message: str, on_click: Optional[Callable[[], None]] = None):
        """Create and display a toast."""
        def _create():
            toast = _Toast(self.root, title, message, on_click)
            self.root.toast_count += 1
            # When toast is destroyed, decrement the count so new toasts stack correctly.
            toast.bind("<Destroy>", lambda e: setattr(self.root, "toast_count", max(0, self.root.toast_count - 1)))
        # Must be executed in the Tk thread.
        self.root.after(0, _create)

    # ----------------------------------------------------------------------- #
    # Public helper methods for the required notification types
    # ----------------------------------------------------------------------- #

    def task_failure(self, task_name: str, error_msg: str):
        title = "Task Failure"
        message = f"Task \"{task_name}\" failed: {error_msg}"
        self._show_toast(title, message, on_click=lambda: self._expand_message(title, message))

    def budget_warning(self, percent_used: float, budget_limit: float):
        title = "Budget Warning"
        message = f"Budget usage at {percent_used:.1f}% (limit: {budget_limit:.2f}). Consider pausing or scaling back."
        self._show_toast(title, message, on_click=lambda: self._expand_message(title, message))

    def checkpoint_saved(self, checkpoint_path: str):
        title = "Checkpoint Saved"
        message = f"Checkpoint stored at:\n{checkpoint_path}"
        self._show_toast(title, message, on_click=lambda: self._expand_message(title, message))

    def new_task_file(self, file_path: str):
        title = "New Task Detected"
        message = f"New task file discovered:\n{file_path}"
        self._show_toast(title, message, on_click=lambda: self._expand_message(title, message))

    # ----------------------------------------------------------------------- #
    # Helper to show expanded view when a toast is clicked
    # ----------------------------------------------------------------------- #

    def _expand_message(self, title: str, message: str):
        """Show a larger, persistent window with the full message."""
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("400x250")
        win.attributes("-topmost", True)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w")
        txt = tk.Text(frame, wrap="word", font=("Segoe UI", 10))
        txt.insert("1.0", message)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, pady=(5,0))

        ttk.Button(frame, text="Close", command=win.destroy).pack(pady=5)

# --------------------------------------------------------------------------- #
# Convenience singleton for the rest of the codebase
# --------------------------------------------------------------------------- #

notifier = ToastNotifier()

# Example usage (remove or comment out in production)
if __name__ == "__main__":
    import time
    notifier.task_failure("DataImport", "File not found")
    notifier.budget_warning(85.3, 1000.0)
    notifier.checkpoint_saved(r"C:\checkpoints\ckpt_20260204.pt")
    notifier.new_task_file(r"C:\tasks\new_job.yaml")
    # Keep the script alive long enough to see the toasts
    time.sleep(10)