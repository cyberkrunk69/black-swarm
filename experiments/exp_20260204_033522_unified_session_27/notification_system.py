"""
notification_system.py

A lightweight toast‑style notification manager for the unified session experiments.
The implementation uses the built‑in ``tkinter`` library so it works without external
dependencies.  Notifications appear in the bottom‑right corner, stack vertically,
auto‑dismiss after 5 seconds, and can be clicked to expand for more detail.

Typical usage:

    from notification_system import NotificationManager

    notifier = NotificationManager()
    notifier.task_failure("Task XYZ failed due to timeout.")
    notifier.budget_warning(0.85, "Project Alpha")
    notifier.checkpoint_saved("Checkpoint #12 saved.")
    notifier.new_task_file_detected("/path/to/new_task.py")
"""

import tkinter as tk
import threading
import time
from typing import Callable, List, Optional

# --------------------------------------------------------------------------- #
# Helper: a simple thread‑safe singleton Tk root
# --------------------------------------------------------------------------- #
class _TkRoot:
    """Singleton wrapper around a hidden Tk root."""
    _instance: Optional[tk.Tk] = None
    _lock = threading.Lock()

    @classmethod
    def get_root(cls) -> tk.Tk:
        with cls._lock:
            if cls._instance is None:
                root = tk.Tk()
                root.withdraw()               # hide the main window
                root.attributes("-topmost", True)
                cls._instance = root
            return cls._instance

# --------------------------------------------------------------------------- #
# Core Notification class
# --------------------------------------------------------------------------- #
class _Toast(tk.Toplevel):
    """A single toast window."""

    WIDTH = 300
    HEIGHT = 80
    PADDING = 10
    AUTO_DISMISS_MS = 5000

    def __init__(self, master: tk.Tk, title: str, message: str,
                 on_expand: Optional[Callable[[str], None]] = None):
        super().__init__(master)
        self.title_str = title
        self.message_str = message
        self.on_expand = on_expand

        self.overrideredirect(True)          # no window decorations
        self.attributes("-topmost", True)
        self.configure(bg="#333333")

        # Build UI
        self._build_widgets()
        self._position()

        # Auto‑dismiss timer
        self.after(self.AUTO_DISMISS_MS, self._close)

        # Click handling
        self.bind("<Button-1>", self._handle_click)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._handle_click)

    def _build_widgets(self):
        # Title label
        title_lbl = tk.Label(self, text=self.title_str, font=("Segoe UI", 10, "bold"),
                             bg="#444444", fg="#ffffff", anchor="w")
        title_lbl.pack(fill="x", padx=5, pady=(5, 0))

        # Message label (single‑line preview)
        msg_lbl = tk.Label(self, text=self.message_str, font=("Segoe UI", 9),
                           bg="#333333", fg="#dddddd", anchor="w", justify="left")
        msg_lbl.pack(fill="both", expand=True, padx=5, pady=2)

    def _position(self):
        """Place the toast in the bottom‑right corner, stacking upwards."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Determine current stack offset (managed by NotificationManager)
        offset_y = self.master.notification_manager.get_stack_offset(self)

        x = screen_w - self.WIDTH - self.PADDING
        y = screen_h - self.HEIGHT - self.PADDING - offset_y
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _handle_click(self, event):
        """Expand the toast to show the full message."""
        if self.on_expand:
            self.on_expand(self.message_str)
        # For demo purposes we simply double the height to reveal more text.
        self.geometry(f"{self.WIDTH}x{self.HEIGHT * 2}")

    def _close(self):
        self.destroy()
        # Notify manager to recalculate stack offsets
        if hasattr(self.master, "notification_manager"):
            self.master.notification_manager.remove_toast(self)


# --------------------------------------------------------------------------- #
# Notification Manager
# --------------------------------------------------------------------------- #
class NotificationManager:
    """
    Manages toast notifications.  All toasts are children of a hidden Tk root.
    The manager tracks active toasts to compute stacking offsets.
    """

    STACK_SPACING = 10  # pixels between stacked toasts

    def __init__(self):
        self.root = _TkRoot.get_root()
        # Attach manager to root for easy access from _Toast instances
        self.root.notification_manager = self
        self.active_toasts: List[_Toast] = []
        # Run the Tk mainloop in a daemon thread
        self._start_mainloop_thread()

    # ------------------------------------------------------------------- #
    # Public API – specific notification types
    # ------------------------------------------------------------------- #
    def task_failure(self, message: str):
        self._show_toast("Task Failure", message)

    def budget_warning(self, spent_ratio: float, project_name: str):
        percent = int(spent_ratio * 100)
        msg = f"Budget for '{project_name}' is at {percent}% of the allocated amount."
        self._show_toast("Budget Warning", msg)

    def checkpoint_saved(self, info: str):
        self._show_toast("Checkpoint Saved", info)

    def new_task_file_detected(self, filepath: str):
        self._show_toast("New Task File", f"Detected new task file: {filepath}")

    # ------------------------------------------------------------------- #
    # Core toast handling
    # ------------------------------------------------------------------- #
    def _show_toast(self, title: str, message: str):
        # Ensure UI actions happen on the Tk thread
        def _create():
            toast = _Toast(self.root, title, message, on_expand=self._on_expand)
            self.active_toasts.append(toast)
            # Force geometry update so stacking works correctly
            toast.update_idletasks()
        self.root.after(0, _create)

    def _on_expand(self, full_message: str):
        # Placeholder for future expansion handling (e.g., open a log window)
        print(f"[Toast Expanded] {full_message}")

    # ------------------------------------------------------------------- #
    # Stacking management
    # ------------------------------------------------------------------- #
    def get_stack_offset(self, toast: _Toast) -> int:
        """Calculate vertical offset for the given toast based on current stack."""
        if toast not in self.active_toasts:
            return 0
        idx = self.active_toasts.index(toast)
        offset = idx * (toast.HEIGHT + self.STACK_SPACING)
        return offset

    def remove_toast(self, toast: _Toast):
        """Called by a toast when it closes; re‑position remaining toasts."""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            self._reposition_toasts()

    def _reposition_toasts(self):
        for i, toast in enumerate(self.active_toasts):
            # Re‑calculate geometry for each toast
            screen_w = toast.winfo_screenwidth()
            screen_h = toast.winfo_screenheight()
            x = screen_w - toast.WIDTH - toast.PADDING
            y = screen_h - toast.HEIGHT - toast.PADDING - i * (toast.HEIGHT + self.STACK_SPACING)
            toast.geometry(f"{toast.WIDTH}x{toast.HEIGHT}+{x}+{y}")

    # ------------------------------------------------------------------- #
    # Tk mainloop handling
    # ------------------------------------------------------------------- #
    def _start_mainloop_thread(self):
        """Run Tk's mainloop in a background daemon thread."""
        def _run():
            try:
                self.root.mainloop()
            except Exception as e:
                print(f"[NotificationManager] Tk mainloop exited with error: {e}")

        thread = threading.Thread(target=_run, name="TkMainloopThread", daemon=True)
        thread.start()


# --------------------------------------------------------------------------- #
# Convenience singleton for importers
# --------------------------------------------------------------------------- #
_notifier_instance: Optional[NotificationManager] = None

def get_notifier() -> NotificationManager:
    """Return a shared NotificationManager instance."""
    global _notifier_instance
    if _notifier_instance is None:
        _notifier_instance = NotificationManager()
    return _notifier_instance

# --------------------------------------------------------------------------- #
# Example usage when run as a script (can be removed in production)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    notifier = get_notifier()
    notifier.task_failure("Example failure: unable to connect to DB.")
    notifier.budget_warning(0.92, "Alpha Project")
    notifier.checkpoint_saved("Checkpoint #42 saved at 2026‑02‑04 12:34.")
    notifier.new_task_file_detected("/tmp/new_task.py")
    # Keep the script alive long enough to see the toasts
    time.sleep(10)