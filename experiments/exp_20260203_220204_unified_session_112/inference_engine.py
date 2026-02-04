import time
import json
import random
import threading
from collections import defaultdict, deque
from typing import Any, Callable, Dict, List, Tuple

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RATE_LIMIT_LOG_PATH = "experiments/exp_20260203_220204_unified_session_112/rate_limit_log.json"

# Exponential back‑off parameters
INITIAL_BACKOFF = 1.0          # seconds
MAX_BACKOFF = 60.0             # seconds
BACKOFF_MULTIPLIER = 2.0

# Sliding window for latency statistics (seconds)
LATENCY_WINDOW = 300           # 5 minutes

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_log() -> List[Dict[str, Any]]:
    """Load the JSON log file, creating it if missing."""
    try:
        with open(RATE_LIMIT_LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _append_log(entry: Dict[str, Any]) -> None:
    """Append a single entry to the rate‑limit log atomically."""
    log = _load_log()
    log.append(entry)
    # Write back in one shot to avoid partial writes.
    with open(RATE_LIMIT_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)


# ----------------------------------------------------------------------
# RateLimiter implementation
# ----------------------------------------------------------------------
class RateLimiter:
    """
    Adaptive rate‑limiter that:
      * Tracks per‑engine latency (sliding window)
      * Detects HTTP 429 responses and applies exponential back‑off
      * Selects the best engine for the next request
      * Persists decisions to a JSON log for observability
    """

    def __init__(self, engines: List[str]) -> None:
        self.engines = engines
        # Deque of (timestamp, latency) per engine
        self.latency_history: Dict[str, deque] = {
            engine: deque(maxlen=1000) for engine in engines
        }
        # Back‑off state: engine -> (backoff_until, current_backoff)
        self.backoff_state: Dict[str, Tuple[float, float]] = {
            engine: (0.0, 0.0) for engine in engines
        }
        self.lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def record_success(self, engine: str, latency: float) -> None:
        """Record a successful call (non‑429) with its latency."""
        now = time.time()
        with self.lock:
            self.latency_history[engine].append((now, latency))
            # Reset back‑off on success
            self.backoff_state[engine] = (0.0, 0.0)

        _append_log({
            "timestamp": now,
            "engine": engine,
            "event": "success",
            "latency": latency,
            "backoff_until": 0.0
        })

    def record_rate_limit(self, engine: str) -> None:
        """Record a 429 response and increase back‑off."""
        now = time.time()
        with self.lock:
            _, current_backoff = self.backoff_state[engine]
            if current_backoff == 0.0:
                new_backoff = INITIAL_BACKOFF
            else:
                new_backoff = min(current_backoff * BACKOFF_MULTIPLIER, MAX_BACKOFF)
            backoff_until = now + new_backoff
            self.backoff_state[engine] = (backoff_until, new_backoff)

        _append_log({
            "timestamp": now,
            "engine": engine,
            "event": "rate_limit",
            "latency": None,
            "backoff_until": backoff_until,
            "backoff_seconds": new_backoff
        })

    def choose_engine(self) -> str:
        """
        Pick the engine with the lowest recent average latency that is not
        currently in back‑off. If all are throttled, pick the one whose
        back‑off expires soonest.
        """
        now = time.time()
        with self.lock:
            # Filter engines that are not throttled
            available = [
                engine for engine, (until, _) in self.backoff_state.items()
                if until <= now
            ]

            if not available:
                # All engines are throttled – pick the one with the smallest
                # remaining back‑off time.
                engine = min(
                    self.backoff_state.items(),
                    key=lambda item: item[1][0]  # backoff_until
                )[0]
                _append_log({
                    "timestamp": now,
                    "engine": engine,
                    "event": "forced_choice_all_throttled",
                    "latency": None,
                    "backoff_until": self.backoff_state[engine][0]
                })
                return engine

            # Compute average latency over the sliding window for each available engine
            avg_latencies = {}
            cutoff = now - LATENCY_WINDOW
            for engine in available:
                latencies = [
                    lat for ts, lat in self.latency_history[engine]
                    if ts >= cutoff
                ]
                avg_latencies[engine] = sum(latencies) / len(latencies) if latencies else float('inf')

            # Choose the engine with the smallest average latency
            best_engine = min(avg_latencies, key=avg_latencies.get)

            _append_log({
                "timestamp": now,
                "engine": best_engine,
                "event": "engine_selected",
                "latency": None,
                "average_latency": avg_latencies[best_engine],
                "backoff_until": self.backoff_state[best_engine][0]
            })
            return best_engine

    # ------------------------------------------------------------------
    # Convenience wrapper for calling a request function
    # ------------------------------------------------------------------
    def call(self, request_fn: Callable[[str], Any]) -> Tuple[Any, str]:
        """
        Executes ``request_fn`` with the selected engine.
        ``request_fn`` must accept a single argument – the engine name – and
        return a tuple ``(response, status_code)`` where ``status_code`` is an
        HTTP‑style integer (e.g., 200 or 429).

        Returns:
            (response, engine_used)
        """
        engine = self.choose_engine()
        start = time.time()
        try:
            response, status = request_fn(engine)
        except Exception as exc:
            # Treat unexpected exceptions as failures but do not back‑off.
            latency = time.time() - start
            self.record_success(engine, latency)  # record latency for diagnostics
            raise

        latency = time.time() - start

        if status == 429:
            self.record_rate_limit(engine)
        else:
            self.record_success(engine, latency)

        return response, engine


# ----------------------------------------------------------------------
# Example usage (to be imported by the rest of the codebase)
# ----------------------------------------------------------------------
# The real inference functions live elsewhere (e.g., groq_inference.py,
# claude_inference.py, together_inference.py).  They should be wrapped
# with ``RateLimiter.call`` like so:

# from .groq_inference import groq_query
# from .claude_inference import claude_query
# from .together_inference import together_query

# _ENGINE_FUNCS = {
#     "groq": groq_query,
#     "claude": claude_query,
#     "together": together_query,
# }

# _rate_limiter = RateLimiter(list(_ENGINE_FUNCS.keys()))

# def unified_query(payload: dict) -> dict:
#     """
#     Dispatch ``payload`` to the best available engine respecting
#     adaptive rate‑limiting.
#     """
#     def _request(engine_name: str):
#         # Each engine function is expected to return (response_dict, http_status)
#         return _ENGINE_FUNCS[engine_name](payload)

#     response, used_engine = _rate_limiter.call(_request)
#     response["engine_used"] = used_engine
#     return response

# ----------------------------------------------------------------------
# End of file
# ----------------------------------------------------------------------