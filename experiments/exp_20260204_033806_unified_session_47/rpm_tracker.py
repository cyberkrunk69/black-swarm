"""
rpm_tracker.py

Utility to track and throttle API request rates per provider.
Supports:
- Groq (30 RPM)
- Together (60 RPM)

Provides:
- utilization()   → current usage ratio (0‑1) per provider
- should_batch()  → True if we are near the limit and should batch requests
- can_call()      → True if a new request can be sent immediately
- wait_time()     → Seconds to wait before the next request is allowed
"""

from __future__ import annotations

import time
import threading
from collections import deque
from typing import Deque, Dict, Tuple


class RPMTracker:
    """
    Tracks requests per minute (RPM) for multiple providers and offers
    helper methods to avoid exceeding provider limits.

    The implementation uses a sliding‑window counter: timestamps of the
    last minute are kept in a deque; the length of the deque equals the
    number of calls made in the current minute.
    """

    # Provider‑specific limits (requests per minute)
    _LIMITS: Dict[str, int] = {
        "groq": 30,
        "together": 60,
    }

    # Threshold at which we start recommending batching (e.g. 80% of limit)
    _BATCH_THRESHOLD = 0.8

    def __init__(self) -> None:
        # Mapping provider → deque of timestamps (seconds since epoch)
        self._calls: Dict[str, Deque[float]] = {
            provider: deque() for provider in self._LIMITS
        }
        # Simple lock to make the tracker thread‑safe
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _prune(self, provider: str, now: float) -> None:
        """
        Remove timestamps older than 60 seconds from the provider's deque.
        """
        window = 60.0
        dq = self._calls[provider]
        while dq and now - dq[0] > window:
            dq.popleft()

    def _record(self, provider: str, now: float) -> None:
        """
        Record a new request timestamp for ``provider``.
        """
        self._calls[provider].append(now)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def utilization(self, provider: str) -> float:
        """
        Return the current utilization ratio (0‑1) for ``provider``.
        If the provider is unknown, raises ``KeyError``.
        """
        now = time.time()
        with self._lock:
            self._prune(provider, now)
            used = len(self._calls[provider])
        limit = self._LIMITS[provider]
        return used / limit

    def can_call(self, provider: str) -> bool:
        """
        Return ``True`` if a new request can be sent immediately without
        exceeding the provider's RPM limit.
        """
        now = time.time()
        with self._lock:
            self._prune(provider, now)
            return len(self._calls[provider]) < self._LIMITS[provider]

    def wait_time(self, provider: str) -> float:
        """
        Return the number of seconds to wait before another request can be
        made without violating the limit. Returns 0 if a call is currently
        allowed.
        """
        now = time.time()
        with self._lock:
            self._prune(provider, now)
            dq = self._calls[provider]
            if len(dq) < self._LIMITS[provider]:
                return 0.0
            # Oldest call in the current window determines when we are free
            oldest = dq[0]
            return max(0.0, 60.0 - (now - oldest))

    def should_batch(self, provider: str) -> bool:
        """
        Return ``True`` if we are approaching the limit and should consider
        batching further requests. The default threshold is 80 % of the RPM
        limit.
        """
        return self.utilization(provider) >= self._BATCH_THRESHOLD

    def register_call(self, provider: str) -> None:
        """
        Record that a request has just been sent to ``provider``.
        This method should be called *after* the request is dispatched.
        """
        now = time.time()
        with self._lock:
            self._prune(provider, now)
            self._record(provider, now)

    # --------------------------------------------------------------------- #
    # Convenience helpers for typical usage patterns
    # --------------------------------------------------------------------- #
    def acquire(self, provider: str) -> Tuple[bool, float]:
        """
        Attempt to acquire permission to call ``provider``.
        Returns a tuple ``(can_call, wait_seconds)``.
        - ``can_call`` is True if the call can proceed immediately.
        - ``wait_seconds`` is 0 if ``can_call`` is True; otherwise the
          time that should be slept before retrying.
        """
        can = self.can_call(provider)
        wait = 0.0 if can else self.wait_time(provider)
        return can, wait

    def reset(self) -> None:
        """
        Clear all recorded timestamps (useful for testing).
        """
        with self._lock:
            for dq in self._calls.values():
                dq.clear()


# ------------------------------------------------------------------------- #
# Module‑level singleton – convenient for projects that need a single tracker
# ------------------------------------------------------------------------- #
_default_tracker = RPMTracker()


def utilization(provider: str) -> float:
    return _default_tracker.utilization(provider)


def can_call(provider: str) -> bool:
    return _default_tracker.can_call(provider)


def wait_time(provider: str) -> float:
    return _default_tracker.wait_time(provider)


def should_batch(provider: str) -> bool:
    return _default_tracker.should_batch(provider)


def register_call(provider: str) -> None:
    _default_tracker.register_call(provider)


def acquire(provider: str) -> Tuple[bool, float]:
    return _default_tracker.acquire(provider)


def reset() -> None:
    _default_tracker.reset()


__all__ = [
    "RPMTracker",
    "utilization",
    "can_call",
    "wait_time",
    "should_batch",
    "register_call",
    "acquire",
    "reset",
]