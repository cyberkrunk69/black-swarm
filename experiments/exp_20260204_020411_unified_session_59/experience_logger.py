import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# Thread‑safe singleton logger for capturing self‑experience data during response generation.
class ExperienceLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_dir: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExperienceLogger, cls).__new__(cls)
                cls._instance._initialize(log_dir)
            return cls._instance

    def _initialize(self, log_dir: Optional[str]) -> None:
        self.log_dir = log_dir or os.getenv("EXPERIENCE_LOG_DIR", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(self.log_dir, f"experience_{timestamp}.jsonl")
        self._file_lock = threading.Lock()

    def log(self, entry: Dict[str, Any]) -> None:
        """Append a JSON‑serializable entry to the log file."""
        if not isinstance(entry, dict):
            raise ValueError("Log entry must be a dictionary")
        # Ensure timestamps are present
        entry.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
        line = json.dumps(entry, ensure_ascii=False)
        with self._file_lock, open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def bulk_log(self, entries: List[Dict[str, Any]]) -> None:
        """Write multiple entries atomically."""
        if not all(isinstance(e, dict) for e in entries):
            raise ValueError("All bulk entries must be dictionaries")
        lines = [
            json.dumps({**e, "timestamp": e.get("timestamp", datetime.utcnow().isoformat() + "Z")}, ensure_ascii=False)
            for e in entries
        ]
        with self._file_lock, open(self.log_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def get_log_path(self) -> str:
        """Return the absolute path to the current log file."""
        return os.path.abspath(self.log_path)


# Convenience singleton accessor
def get_experience_logger() -> ExperienceLogger:
    return ExperienceLogger()