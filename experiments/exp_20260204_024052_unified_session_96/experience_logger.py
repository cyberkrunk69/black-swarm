import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List

# Thread‑safe singleton logger for self‑experience data
class ExperienceLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, log_dir: str = "logs/experience"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ExperienceLogger, cls).__new__(cls)
                cls._instance._init(log_dir)
            return cls._instance

    def _init(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self._file_path = os.path.join(
            self.log_dir,
            f"experience_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.jsonl"
        )
        self._file_lock = threading.Lock()

    def _write_record(self, record: Dict[str, Any]) -> None:
        line = json.dumps(record, ensure_ascii=False)
        with self._file_lock, open(self._file_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log(
        self,
        *,
        request_id: str,
        user_prompt: str,
        model_output: str,
        metadata: Dict[str, Any] = None,
        timestamp: float = None,
    ) -> None:
        """
        Record a single interaction.

        Parameters
        ----------
        request_id: str
            Unique identifier for the request/response pair.
        user_prompt: str
            The raw prompt received from the user.
        model_output: str
            The generated response.
        metadata: dict, optional
            Additional contextual data (e.g., token usage, latency).
        timestamp: float, optional
            Unix epoch time; defaults to ``time.time()``.
        """
        record = {
            "request_id": request_id,
            "timestamp": timestamp or time.time(),
            "user_prompt": user_prompt,
            "model_output": model_output,
            "metadata": metadata or {},
        }
        self._write_record(record)

# Helper function for quick usage throughout the codebase
def log_experience(
    request_id: str,
    user_prompt: str,
    model_output: str,
    metadata: Dict[str, Any] = None,
) -> None:
    """
    Convenience wrapper that obtains the singleton logger and writes a record.
    """
    logger = ExperienceLogger()
    logger.log(
        request_id=request_id,
        user_prompt=user_prompt,
        model_output=model_output,
        metadata=metadata,
    )

# ----------------------------------------------------------------------
# Integration hook
# ----------------------------------------------------------------------
# The main response generation pipeline (e.g., ``/app/pipeline.py`` or similar)
# should import this module and invoke ``log_experience`` after producing a
# response. Example usage:
#
#   from experiments.exp_20260204_024052_unified_session_96.experience_logger import log_experience
#
#   def generate_response(request):
#       response = model.generate(request.prompt)
#       log_experience(
#           request_id=request.id,
#           user_prompt=request.prompt,
#           model_output=response,
#           metadata={"latency_ms": response.latency, "tokens_used": response.token_count},
#       )
#       return response
#
# The above snippet is illustrative; actual integration points should call
# ``log_experience`` wherever the final model output is ready to be returned.