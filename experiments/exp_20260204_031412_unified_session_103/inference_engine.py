"""
Adaptive Rate Limiting for Inference Engines

This module wraps the existing engine clients (Groq, Claude, Together) with
adaptive rate‑limiting logic. It tracks per‑engine response times and HTTP
429 (Too Many Requests) responses, applying exponential back‑off when limits
are hit. Load is automatically distributed across the healthy engines.

All decisions (selected engine, back‑off duration, errors) are logged to
`rate_limit_log.json` in the experiment directory.
"""

import json
import time
import threading
from collections import defaultdict
from typing import Any, Callable, Dict, List

# --------------------------------------------------------------------------- #
# Placeholder imports – replace with your actual engine client imports.
# --------------------------------------------------------------------------- #
# from your_project.groq_client import GroqClient
# from your_project.claude_client import ClaudeClient
# from your_project.together_client import TogetherClient

# For demonstration we define minimal stub clients.
class _BaseClient:
    def __init__(self, name: str):
        self.name = name

    def infer(self, payload: Dict) -> Dict:
        """
        Simulate an inference request.
        Replace this stub with the real API call.
        """
        # Simulated response: random 200 or 429 for demo.
        import random
        if random.random() < 0.1:  # 10% chance of rate limit
            raise RateLimitError(429, "Rate limit exceeded")
        # Simulate variable latency
        latency = random.uniform(0.05, 0.3)
        time.sleep(latency)
        return {"engine": self.name, "payload": payload, "latency": latency}

class GroqClient(_BaseClient):
    pass

class ClaudeClient(_BaseClient):
    pass

class TogetherClient(_BaseClient):
    pass

# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #
class RateLimitError(Exception):
    """Raised when an engine returns HTTP 429."""
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code

# --------------------------------------------------------------------------- #
# Rate Limiter
# --------------------------------------------------------------------------- #
class AdaptiveRateLimiter:
    """
    Tracks per‑engine metrics and decides which engine to use for the next request.
    Implements exponential back‑off on 429 responses.
    """

    LOG_PATH = "experiments/exp_20260204_031412_unified_session_103/rate_limit_log.json"

    def __init__(self, engines: Dict[str, Callable[[Dict], Dict]], base_backoff: float = 1.0,
                 max_backoff: float = 60.0, backoff_factor: float = 2.0):
        """
        :param engines: Mapping of engine name -> callable that performs inference.
        :param base_backoff: Initial back‑off in seconds.
        :param max_backoff: Upper bound for back‑off.
        :param backoff_factor: Exponential factor.
        """
        self.engines = engines
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.backoff_factor = backoff_factor

        # Runtime state
        self.lock = threading.Lock()
        self.backoff_until: Dict[str, float] = defaultdict(lambda: 0.0)
        self.consecutive_429: Dict[str, int] = defaultdict(int)
        self.avg_latency: Dict[str, float] = defaultdict(lambda: 0.0)
        self.latency_samples: Dict[str, List[float]] = defaultdict(list)

        # Initialise log file
        self._init_log()

    # ------------------------------------------------------------------- #
    # Logging helpers
    # ------------------------------------------------------------------- #
    def _init_log(self):
        try:
            with open(self.LOG_PATH, "x") as f:
                json.dump([], f)
        except FileExistsError:
            pass  # Log already exists

    def _append_log(self, entry: Dict[str, Any]):
        with self.lock:
            try:
                with open(self.LOG_PATH, "r+") as f:
                    data = json.load(f)
                    data.append(entry)
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
            except Exception as e:
                # Logging must never crash the main flow.
                print(f"[RateLimiter] Failed to write log entry: {e}")

    # ------------------------------------------------------------------- #
    # Core algorithm
    # ------------------------------------------------------------------- #
    def _is_engine_available(self, name: str) -> bool:
        return time.time() >= self.backoff_until[name]

    def _select_engine(self) -> str:
        """
        Choose the best available engine based on current back‑off state and
        observed latency. Engines under back‑off are ignored.
        """
        with self.lock:
            candidates = [n for n in self.engines if self._is_engine_available(n)]
            if not candidates:
                # All engines are cooling down – pick the one with the shortest
                # remaining back‑off.
                soonest = min(self.engines.keys(),
                              key=lambda n: self.backoff_until[n])
                return soonest

            # Prefer lower average latency; fall back to random order if no data.
            def latency_key(name):
                return self.avg_latency[name] if self.latency_samples[name] else float('inf')

            candidates.sort(key=latency_key)
            return candidates[0]

    def _record_success(self, engine: str, latency: float):
        with self.lock:
            self.latency_samples[engine].append(latency)
            # Keep a rolling window of the last 20 samples to bound memory.
            if len(self.latency_samples[engine]) > 20:
                self.latency_samples[engine].pop(0)
            self.avg_latency[engine] = sum(self.latency_samples[engine]) / len(self.latency_samples[engine])
            # Reset 429 counters on success.
            self.consecutive_429[engine] = 0
            self.backoff_until[engine] = 0.0

    def _record_rate_limit(self, engine: str):
        with self.lock:
            self.consecutive_429[engine] += 1
            backoff = min(self.base_backoff * (self.backoff_factor ** (self.consecutive_429[engine] - 1)),
                          self.max_backoff)
            self.backoff_until[engine] = time.time() + backoff

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def infer(self, payload: Dict) -> Dict:
        """
        Perform inference using the best available engine, handling back‑off
        automatically. Returns the raw response from the underlying engine.
        """
        attempt = 0
        while True:
            engine_name = self._select_engine()
            client_callable = self.engines[engine_name]

            start = time.time()
            try:
                response = client_callable(payload)
                latency = time.time() - start
                self._record_success(engine_name, latency)

                log_entry = {
                    "timestamp": time.time(),
                    "engine": engine_name,
                    "status": "success",
                    "latency": latency,
                    "payload": payload,
                    "attempt": attempt
                }
                self._append_log(log_entry)
                return response

            except RateLimitError as e:
                # Record back‑off and retry with another engine.
                self._record_rate_limit(engine_name)
                log_entry = {
                    "timestamp": time.time(),
                    "engine": engine_name,
                    "status": "rate_limited",
                    "error": str(e),
                    "payload": payload,
                    "attempt": attempt
                }
                self._append_log(log_entry)
                attempt += 1
                # Small sleep to avoid tight loop when all engines are throttled.
                time.sleep(0.1)
                continue

            except Exception as e:
                # Unexpected errors are logged but not retried here.
                latency = time.time() - start
                log_entry = {
                    "timestamp": time.time(),
                    "engine": engine_name,
                    "status": "error",
                    "error": str(e),
                    "latency": latency,
                    "payload": payload,
                    "attempt": attempt
                }
                self._append_log(log_entry)
                raise  # Propagate upwards for caller handling.

# --------------------------------------------------------------------------- #
# Engine client initialization
# --------------------------------------------------------------------------- #
# Instantiate real clients here. Replace the stubs with your actual SDK objects.
_groq_client = GroqClient("groq")
_claude_client = ClaudeClient("claude")
_together_client = TogetherClient("together")

# Mapping from engine name to a callable that performs inference.
_ENGINE_CALLABLES: Dict[str, Callable[[Dict], Dict]] = {
    "groq": _groq_client.infer,
    "claude": _claude_client.infer,
    "together": _together_client.infer,
}

# Create a singleton rate limiter for the process.
_rate_limiter = AdaptiveRateLimiter(_ENGINE_CALLABLES)

# --------------------------------------------------------------------------- #
# Public wrapper function used by the rest of the codebase.
# --------------------------------------------------------------------------- #
def infer(payload: Dict) -> Dict:
    """
    Public entry point used by the application. Delegates to the adaptive
    rate limiter which decides the optimal engine and handles back‑off.
    """
    return _rate_limiter.infer(payload)

# --------------------------------------------------------------------------- #
# Example usage (remove or comment out in production)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    test_payload = {"prompt": "Explain adaptive rate limiting in 2 sentences."}
    try:
        result = infer(test_payload)
        print("Result:", result)
    except Exception as exc:
        print("Inference failed:", exc)