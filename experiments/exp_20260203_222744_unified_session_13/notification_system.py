"""
notification_system.py

A lightweight toast‑style notification system for the Claude Parasite Brain Suck project.
Supports:
- Task failure alerts
- Budget usage warnings (>80% spent)
- Checkpoint save confirmations
- New task file detections

Features:
- Stacks notifications in the bottom‑right corner of the primary screen.
- Auto‑dismisses after 5 seconds.
- Click to expand for more details (toggles between compact and expanded view).
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Callable, Optional

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_DURATION_MS = 5000          # Auto‑dismiss after 5 seconds
STACK_MARGIN = 10                   # Pixels between stacked toasts
TOAST_WIDTH = 300
TOAST_HEIGHT_COMPACT = 80
TOAST_HEIGHT_EXPANDED = 200
BG_COLOR = "#333333"
FG_COLOR = "#FFFFFF"
FONT = ("Segoe UI", 10)
EXPAND_FONT = ("Segoe UI", 9)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _run_on_main_thread(func: Callable, *args, **kwargs):
    """Schedule a callable to run on the Tkinter main loop."""
    root = tk._default_root
    if root:
        root.after(0, func, *args, **kwargs)
    else:
        # If no root exists yet, start one in a new thread.
        threading.Thread(target=_bootstrap_root_and_run, args=(func, args, kwargs), daemon=True).start()

def _bootstrap_root_and_run(func: Callable, args, kwargs):
    root = tk.Tk()
    root.withdraw()  # hide the root window
    func(*args, **kwargs)
    root.mainloop()


# ----------------------------------------------------------------------
# Toast implementation
# ----------------------------------------------------------------------
class Toast(tk.Toplevel):
    """A single toast notification."""

    _stack = []  # class‑level list of active toasts for stacking

    def __init__(self, title: str, message: str, icon: Optional[str] = None,
                 duration_ms: int = DEFAULT_DURATION_MS):
        super().__init__(tk._default_root)
        self.title_text = title
        self.message_text = message
        self.icon_path = icon
        self.duration_ms = duration_ms
        self.expanded = False

        self._setup_window()
        self._populate()
        self._position()
        self._schedule_dismiss()

        # Register for stacking
        Toast._stack.append(self)

        # Bind click to toggle expand/collapse
        self.bind("<Button-1>", self._toggle_expand)
        self.message_label.bind("<Button-1>", self._toggle_expand)

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------
    def _setup_window(self):
        self.overrideredirect(True)  # No window decorations
        self.configure(background=BG_COLOR)
        self.attributes("-topmost", True)
        self.geometry(f"{TOAST_WIDTH}x{TOAST_HEIGHT_COMPACT}+0+0")  # placeholder, will be repositioned

    # ------------------------------------------------------------------
    # UI population
    # ------------------------------------------------------------------
    def _populate(self):
        # Title
        self.title_label = ttk.Label(self, text=self.title_text, foreground=FG_COLOR,
                                     background=BG_COLOR, font=("Segoe UI", 11, "bold"))
        self.title_label.pack(padx=10, pady=(8, 0), anchor="w")

        # Message (initially compact)
        self.message_label = ttk.Label(self, text=self.message_text, foreground=FG_COLOR,
                                       background=BG_COLOR, font=FONT, wraplength=TOAST_WIDTH-20,
                                       justify="left")
        self.message_label.pack(padx=10, pady=5, anchor="w")

    # ------------------------------------------------------------------
    # Positioning / stacking
    # ------------------------------------------------------------------
    def _position(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Bottom‑right corner, accounting for existing stacked toasts
        total_offset = sum(t.winfo_height() + STACK_MARGIN for t in Toast._stack if t is not self)
        x = screen_width - TOAST_WIDTH - STACK_MARGIN
        y = screen_height - TOAST_HEIGHT_COMPACT - STACK_MARGIN - total_offset
        self.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Auto‑dismiss handling
    # ------------------------------------------------------------------
    def _schedule_dismiss(self):
        self.after(self.duration_ms, self._dismiss)

    def _dismiss(self):
        if self in Toast._stack:
            Toast._stack.remove(self)
        self.destroy()
        # Re‑position remaining toasts
        for toast in Toast._stack:
            toast._position()

    # ------------------------------------------------------------------
    # Expand / collapse toggle
    # ------------------------------------------------------------------
    def _toggle_expand(self, event=None):
        if self.expanded:
            self.geometry(f"{TOAST_WIDTH}x{TOAST_HEIGHT_COMPACT}")
            self.message_label.configure(font=FONT)
        else:
            self.geometry(f"{TOAST_WIDTH}x{TOAST_HEIGHT_EXPANDED}")
            self.message_label.configure(font=EXPAND_FONT)
        self.expanded = not self.expanded
        self._position()  # keep stack consistent

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def _show_toast(title: str, message: str, icon: Optional[str] = None,
                duration_ms: int = DEFAULT_DURATION_MS):
    """Thread‑safe way to create a toast."""
    def _create():
        # Ensure a root window exists
        if not tk._default_root:
            root = tk.Tk()
            root.withdraw()
        Toast(title, message, icon, duration_ms)
    _run_on_main_thread(_create)


def notify_task_failure(task_name: str, error_msg: str):
    """Notify that a task has failed."""
    title = f"❌ Task Failure: {task_name}"
    message = f"Error: {error_msg}"
    _show_toast(title, message)


def notify_budget_warning(percent_used: float, budget_limit: float):
    """Notify when budget usage exceeds 80%."""
    title = "⚠️ Budget Warning"
    message = (f"Budget usage is at {percent_used:.1f}% "
               f"of the allowed {budget_limit:.2f} units.")
    _show_toast(title, message)


def notify_checkpoint_save(checkpoint_name: str, location: str):
    """Notify that a checkpoint has been saved."""
    title = "✅ Checkpoint Saved"
    message = f"'{checkpoint_name}' saved to {location}."
    _show_toast(title, message)


def notify_new_task_file(file_path: str):
    """Notify that a new task file has been detected."""
    title = "📄 New Task File"
    message = f"Detected new task definition: {file_path}"
    _show_toast(title, message)


# ----------------------------------------------------------------------
# Example usage (remove or comment out in production)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple demo showing all notification types
    notify_task_failure("DataIngestion", "Connection timeout after 30s")
    time.sleep(1)
    notify_budget_warning(85.2, 1000.0)
    time.sleep(1)
    notify_checkpoint_save("epoch_12.ckpt", "/models/checkpoints")
    time.sleep(1)
    notify_new_task_file("tasks/new_analysis.yaml")
    # Keep the script alive long enough to see the toasts
    time.sleep(10)