import json
import os
import threading
from datetime import datetime
from typing import Any, Dict

# Thread‑safe singleton logger for self‑experience data
class ExperienceLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_dir: str = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExperienceLogger, cls).__new__(cls)
                cls._instance._initialize(log_dir)
            return cls._instance

    def _initialize(self, log_dir: str):
        # Determine log directory – default to the experiment folder
        if log_dir is None:
            # Resolve relative to this file's location
            base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )
            log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(log_dir, f"self_experience_{timestamp}.jsonl")
        self._file_lock = threading.Lock()

    def log(self, entry: Dict[str, Any]) -> None:
        """Append a JSON‑encoded experience entry to the log file."""
        # Ensure the entry is JSON‑serializable
        entry = dict(entry)  # shallow copy
        entry.setdefault("timestamp_utc", datetime.utcnow().isoformat() + "Z")
        with self._file_lock, open(self.log_path, "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

# Helper decorator to automatically log input/output of functions
def log_experience(func):
    """
    Decorator that logs the function name, its arguments, and the returned
    value using the shared ExperienceLogger instance.
    """
    def wrapper(*args, **kwargs):
        logger = ExperienceLogger()
        entry = {
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs,
        }
        result = func(*args, **kwargs)
        entry["result"] = result
        logger.log(entry)
        return result
    return wrapper