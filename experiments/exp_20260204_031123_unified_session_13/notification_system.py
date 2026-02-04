"""
notification_system.py

A lightweight toast‑style notification system for the unified session experiment.
Features:
- Stackable toast windows in the bottom‑right corner of the primary monitor.
- Auto‑dismiss after 5 seconds.
- Click to expand the toast (show full message and keep it open until manually closed).
- Helper functions for the four required notification types:
    * task failures
    * budget warnings (>80% spent)
    * checkpoint saves
    * new task files detected
"""

import threading
import tkinter as tk
from tkinter import ttk
from typing import List

# --------------------------------------------------------------------------- #
# Core toast implementation
# --------------------------------------------------------------------------- #

class Toast(tk.Toplevel):
    """A single toast window."""
    WIDTH = 300
    HEIGHT = 80
    PADDING = 10
    AUTO_DISMISS_MS = 5000  # 5 seconds

    def __init__(self, master: tk.Tk, title: str, message: str, **kwargs):
        super().__init__(master, **kwargs)
        self.title_text = title
        self.message_text = message
        self.expanded = False

        # Remove window decorations & make it topmost
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # Build UI
        self._build_ui()

        # Position will be set by NotificationManager
        self.update_idletasks()

        # Auto‑dismiss timer
        self.after(self.AUTO_DISMISS_MS, self._auto_dismiss)

        # Click handling
        self.bind("<Button-1>", self._on_click)
        self.title_label.bind("<Button-1>", self._on_click)
        self.message_label.bind("<Button-1>", self._on_click)

    def _build_ui(self):
        self.configure(bg="#333333")
        container = ttk.Frame(self, padding=8, style="Toast.TFrame")
        container.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Toast.TFrame", background="#333333")
        style.configure("Toast.Title.TLabel", foreground="#ffffff", background="#333333", font=("Segoe UI", 10, "bold"))
        style.configure("Toast.Message.TLabel", foreground="#dddddd", background="#333333", font=("Segoe UI", 9))

        self.title_label = ttk.Label(container, text=self.title_text, style="Toast.Title.TLabel")
        self.title_label.pack(anchor="w")
        self.message_label = ttk.Label(container, text=self.message_text, style="Toast.Message.TLabel", wraplength=self.WIDTH-20, justify="left")
        self.message_label.pack(anchor="w", pady=(2, 0))

    def _auto_dismiss(self):
        if not self.expanded:
            self.destroy()

    def _on_click(self, event):
        if not self.expanded:
            # Expand: increase height to fit full message and stop auto‑dismiss
            self.expanded = True
            self.after_cancel(self.after_id) if hasattr(self, 'after_id') else None
            # Re‑wrap message to full width and let the window size itself
            self.message_label.configure(wraplength=self.WIDTH - 20)
            self.update_idletasks()
            # Add a close button
            close_btn = ttk.Button(self, text="✕", command=self.destroy, style="Toast.Close.TButton")
            close_btn.place(relx=1.0, rely=0.0, x=-4, y=4, anchor="ne")
            style = ttk.Style()
            style.configure("Toast.Close.TButton", foreground="#ff6666", background="#333333", borderwidth=0)
        else:
            # If already expanded, close on second click
            self.destroy()

    # Helper for manager to cancel pending auto‑dismiss when expanding
    def pause_auto_dismiss(self):
        self.after_cancel(self.after_id)

# --------------------------------------------------------------------------- #
# Notification manager – handles stacking and convenience API
# --------------------------------------------------------------------------- #

class NotificationManager:
    """Singleton manager for toast notifications."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(NotificationManager, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        # Root Tk instance (hidden)
        self.root = tk.Tk()
        self.root.withdraw()
        self.active_toasts: List[Toast] = []
        # Screen geometry for positioning
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        # Padding from screen edges
        self.margin = 20

    def _reposition_toasts(self):
        """Stack toasts from bottom‑right upwards."""
        y_offset = self.margin
        for toast in reversed(self.active_toasts):
            toast.update_idletasks()
            w = toast.WIDTH
            h = toast.winfo_height()
            x = self.screen_width - w - self.margin
            y = self.screen_height - h - y_offset
            toast.geometry(f"{w}x{h}+{x}+{y}")
            y_offset += h + Toast.PADDING

    def _create_toast(self, title: str, message: str):
        toast = Toast(self.root, title, message)
        self.active_toasts.append(toast)
        self._reposition_toasts()
        # When the toast is destroyed, remove it from the list and reposition others
        toast.bind("<Destroy>", lambda e, t=toast: self._on_toast_destroy(t))
        return toast

    def _on_toast_destroy(self, toast: Toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            self._reposition_toasts()

    # ------------------------------------------------------------------- #
    # Public helper methods for the four required notification types
    # ------------------------------------------------------------------- #

    def notify_task_failure(self, task_name: str, error_msg: str):
        title = "Task Failure"
        message = f"Task '{task_name}' failed.\nError: {error_msg}"
        self._create_toast(title, message)

    def notify_budget_warning(self, percent_used: float, budget_limit: float):
        title = "Budget Warning"
        message = (f"Budget usage at {percent_used:.1f}% (limit: {budget_limit:.1f}). "
                   "Consider reviewing resource allocation.")
        self._create_toast(title, message)

    def notify_checkpoint_save(self, checkpoint_name: str):
        title = "Checkpoint Saved"
        message = f"Checkpoint '{checkpoint_name}' has been saved successfully."
        self._create_toast(title, message)

    def notify_new_task_file(self, file_path: str):
        title = "New Task File Detected"
        message = f"A new task file was detected:\n{file_path}"
        self._create_toast(title, message)

    # ------------------------------------------------------------------- #
    # Utility – start the Tk mainloop in a background thread
    # ------------------------------------------------------------------- #

    def start(self):
        """Start the Tk event loop in a daemon thread (if not already running)."""
        if not hasattr(self, "_loop_thread"):
            self._loop_thread = threading.Thread(target=self.root.mainloop, daemon=True)
            self._loop_thread.start()


# --------------------------------------------------------------------------- #
# Convenience singleton instance
# --------------------------------------------------------------------------- #

notification_manager = NotificationManager()
notification_manager.start()

# --------------------------------------------------------------------------- #
# Example usage (can be removed or left for reference)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import time
    nm = notification_manager
    nm.notify_task_failure("DataImport", "File not found")
    nm.notify_budget_warning(85.2, 100.0)
    nm.notify_checkpoint_save("epoch_12")
    nm.notify_new_task_file("/data/tasks/new_task.yaml")
    # Keep the script alive long enough to see toasts
    time.sleep(10)