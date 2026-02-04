import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# Thread‑safe singleton logger for capturing self‑experience data during response generation.
class SelfExperienceLogger:
    _instance: Optional["SelfExperienceLogger"] = None
    _lock = threading.Lock()

    def __new__(cls, log_dir: str = "logs/experience"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SelfExperienceLogger, cls).__new__(cls)
                cls._instance._initialize(log_dir)
            return cls._instance

    def _initialize(self, log_dir: str) -> None:
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        self.log_path = os.path.join(self.log_dir, f"self_experience_{timestamp}.jsonl")
        self._file_lock = threading.Lock()

    def log(self, entry: Dict[str, Any]) -> None:
        """
        Append a JSON line representing a single experience entry.

        Expected keys (optional, but recommended):
            - "session_id": Unique identifier for the current interaction session.
            - "timestamp": ISO‑8601 UTC timestamp (added automatically if missing).
            - "prompt": The input prompt given to the model.
            - "response": The model's generated response.
            - "metadata": Any auxiliary data (e.g., token usage, latency, user feedback).

        The method is safe to call from multiple threads.
        """
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
        line = json.dumps(entry, ensure_ascii=False)

        with self._file_lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def bulk_log(self, entries: List[Dict[str, Any]]) -> None:
        """Log multiple entries atomically."""
        lines = []
        for entry in entries:
            if "timestamp" not in entry:
                entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
            lines.append(json.dumps(entry, ensure_ascii=False))

        with self._file_lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")

    def get_log_path(self) -> str:
        """Return the absolute path of the current log file."""
        return os.path.abspath(self.log_path)


# Convenience accessor for the global logger instance.
def get_logger() -> SelfExperienceLogger:
    """
    Retrieve the singleton logger instance.
    The first call may optionally specify a custom log directory:

        logger = get_logger()
        # or
        logger = SelfExperienceLogger(log_dir="custom/path")
    """
    return SelfExperienceLogger()


# Example integration hook (to be called from the main response generation pipeline):
def log_self_experience(session_id: str, prompt: str, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Simple wrapper that formats and forwards experience data to the logger.
    """
    entry: Dict[str, Any] = {
        "session_id": session_id,
        "prompt": prompt,
        "response": response,
    }
    if metadata:
        entry["metadata"] = metadata
    get_logger().log(entry)


# If this module is executed directly, demonstrate a quick self‑test.
if __name__ == "__main__":
    demo_logger = get_logger()
    demo_logger.log({
        "session_id": "demo-001",
        "prompt": "Hello, world!",
        "response": "Hi there!",
        "metadata": {"latency_ms": 42}
    })
    print(f"Logged experience to: {demo_logger.get_log_path()}")