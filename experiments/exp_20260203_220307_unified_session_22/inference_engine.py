"""
Adaptive Rate Limiting for Multi‑Engine Inference

This module provides a thin wrapper around the three supported inference back‑ends
(Groq, Claude and Together). It tracks per‑engine response times and HTTP 429
(rate‑limit) responses, automatically backs off exponentially when limits are hit,
and distributes load across the available engines based on their current health.

All decisions (engine selection, back‑off duration, errors) are logged to
`rate_limit_log.json` in the same directory.
"""

import json
import time
import threading
from collections import deque
from pathlib import Path
from typing import Any, Callable, Deque, Dict, List, Optional

import requests

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

LOG_PATH = Path(__file__).with_name("rate_limit_log.json")
MAX_HISTORY = 20                     # Number of recent latencies to keep per engine
BASE_BACKOFF = 1.0                    # Seconds (initial exponential back‑off)
MAX_BACKOFF = 60.0                    # Seconds (cap for exponential back‑off)
ERROR_PENALTY = 5.0                   # Additional seconds added on each 429

# --------------------------------------------------------------------------- #
# Helper – thread‑safe JSON logger
# --------------------------------------------------------------------------- #

_log_lock = threading.Lock()


def _log_decision(entry: Dict[str, Any]) -> None:
    """Append a JSON line to the rate‑limit log file."""
    with _log_lock:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")


# --------------------------------------------------------------------------- #
# Rate‑limiter state per engine
# --------------------------------------------------------------------------- #

class EngineStats:
    """Collects latency & error statistics for a single engine."""

    def __init__(self, name: str):
        self.name = name
        self.latencies: Deque[float] = deque(maxlen=MAX_HISTORY)
        self.consecutive_429: int = 0
        self.backoff_until: float = 0.0  # epoch time when we may retry

    @property
    def avg_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    @property
    def is_backing_off(self) -> bool:
        return time.time() < self.backoff_until

    def record_success(self, latency: float) -> None:
        self.latencies.append(latency)
        self.consecutive_429 = 0
        # Reset back‑off on success
        self.backoff_until = 0.0

    def record_429(self) -> None:
        self.consecutive_429 += 1
        # Exponential back‑off: base * 2^(n-1) + error penalty
        backoff = min(
            BASE_BACKOFF * (2 ** (self.consecutive_429 - 1)) + ERROR_PENALTY,
            MAX_BACKOFF,
        )
        self.backoff_until = time.time() + backoff
        _log_decision({
            "timestamp": time.time(),
            "engine": self.name,
            "event": "429_backoff",
            "consecutive_429": self.consecutive_429,
            "backoff_seconds": backoff,
        })


# --------------------------------------------------------------------------- #
# Central manager
# --------------------------------------------------------------------------- #

class AdaptiveRateLimiter:
    """Manages multiple inference engines and applies adaptive back‑off."""

    def __init__(self):
        self.engines: Dict[str, Callable[[Dict[str, Any]], Any]] = {
            "groq": self._call_groq,
            "claude": self._call_claude,
            "together": self._call_together,
        }
        self.stats: Dict[str, EngineStats] = {
            name: EngineStats(name) for name in self.engines
        }
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def infer(self, payload: Dict[str, Any]) -> Any:
        """
        Choose the best engine, invoke it, and handle rate‑limit back‑off.
        Returns the raw response from the selected engine.
        """
        engine_name = self._select_engine()
        if engine_name is None:
            raise RuntimeError("All engines are currently backing off. Try later.")

        engine_func = self.engines[engine_name]
        stats = self.stats[engine_name]

        start = time.time()
        try:
            response = engine_func(payload)
            latency = time.time() - start
            stats.record_success(latency)

            _log_decision({
                "timestamp": start,
                "engine": engine_name,
                "event": "success",
                "latency": latency,
                "payload_summary": self._summarise_payload(payload),
            })
            return response

        except requests.HTTPError as exc:
            if exc.response.status_code == 429:
                stats.record_429()
                # Immediately retry with a different engine (if possible)
                _log_decision({
                    "timestamp": time.time(),
                    "engine": engine_name,
                    "event": "429_received",
                    "payload_summary": self._summarise_payload(payload),
                })
                # Recursive retry – depth limited to avoid infinite loops
                return self._retry_with_alternative(engine_name, payload, depth=1)
            else:
                # Propagate other HTTP errors
                raise

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _retry_with_alternative(self, failed_engine: str, payload: Dict[str, Any], depth: int) -> Any:
        """Attempt to route the request to another engine after a 429."""
        if depth > len(self.engines):
            raise RuntimeError("Exhausted all engines after rate‑limit retries.")
        next_engine = self._select_engine(exclude={failed_engine})
        if not next_engine:
            raise RuntimeError("No alternative engine available for retry.")
        return self.infer(payload)  # reuse public method – will pick the new engine

    def _select_engine(self, exclude: Optional[set] = None) -> Optional[str]:
        """
        Choose the engine with the lowest estimated latency that is not backing off.
        `exclude` can be used to ignore specific engines (e.g., the one that just 429'd).
        """
        with self._lock:
            candidates = [
                (stats.avg_latency, name)
                for name, stats in self.stats.items()
                if not stats.is_backing_off and (exclude is None or name not in exclude)
            ]
            if not candidates:
                return None
            # Sort by avg latency (lower is better); tie‑break by name for determinism
            candidates.sort()
            chosen_name = candidates[0][1]
            _log_decision({
                "timestamp": time.time(),
                "engine": chosen_name,
                "event": "engine_selected",
                "reason": "lowest_latency",
                "avg_latency": self.stats[chosen_name].avg_latency,
            })
            return chosen_name

    @staticmethod
    def _summarise_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Return a trimmed representation suitable for logging."""
        summary = {k: (v if len(str(v)) < 200 else f"<truncated {len(str(v))} chars>")
                   for k, v in payload.items()}
        return summary

    # --------------------------------------------------------------------- #
    # Stubbed engine call implementations
    # --------------------------------------------------------------------- #
    # In a real project these would import the actual SDKs / HTTP wrappers.
    # They are kept minimal here to keep the example self‑contained.

    def _call_groq(self, payload: Dict[str, Any]) -> Any:
        # Placeholder: replace with actual Groq SDK call
        url = "https://api.groq.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self._get_api_key('groq')}"}
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _call_claude(self, payload: Dict[str, Any]) -> Any:
        # Placeholder: replace with actual Claude SDK call
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": self._get_api_key('claude'), "Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _call_together(self, payload: Dict[str, Any]) -> Any:
        # Placeholder: replace with actual Together SDK call
        url = "https://api.together.xyz/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self._get_api_key('together')}"}
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _get_api_key(engine_name: str) -> str:
        """Fetch API key from environment variables (simple stub)."""
        import os

        env_var = {
            "groq": "GROQ_API_KEY",
            "claude": "CLAUDE_API_KEY",
            "together": "TOGETHER_API_KEY",
        }.get(engine_name)

        if not env_var:
            raise ValueError(f"Unknown engine {engine_name}")

        key = os.getenv(env_var)
        if not key:
            raise RuntimeError(f"Missing environment variable {env_var} for {engine_name}")
        return key


# --------------------------------------------------------------------------- #
# Convenience singleton for the rest of the codebase
# --------------------------------------------------------------------------- #

rate_limiter = AdaptiveRateLimiter()


def infer(payload: Dict[str, Any]) -> Any:
    """
    Public function used by other modules.
    Example:
        response = inference_engine.infer({"model": "...", "messages": [...]})
    """
    return rate_limiter.infer(payload)