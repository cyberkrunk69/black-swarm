"""
rpm_tracker.py

Utility for tracking and managing per‑minute request limits for different LLM providers.
Supports Groq (30 RPM) and Together (60 RPM) with adaptive batching logic.

Typical usage:

    from rpm_tracker import RPMTracker

    rpm = RPMTracker()
    if rpm.can_call('groq'):
        # make a request
        rpm.record_call('groq')
    else:
        # either wait or batch
        time_to_wait = rpm.wait_time('groq')
        ...

The tracker is thread‑safe and can be shared across the application.
"""

import time
import threading
from collections import deque
from typing import Deque, Dict, List

# ---------------------------------------------------------------------------
# Configuration – per‑provider limits (requests per minute)
# ---------------------------------------------------------------------------
_PROVIDER_LIMITS: Dict[str, int] = {
    "groq": 30,      # 30 requests per minute
    "together": 60,  # 60 requests per minute
}

# Threshold (as a fraction of the limit) at which we start recommending batching.
_BATCHING_THRESHOLD = 0.8  # 80% of the RPM limit


class RPMTracker:
    """
    Tracks request timestamps for each provider and offers helpers for
    - current utilization (percentage of the minute's quota used)
    - whether we should batch requests
    - whether a new request can be sent immediately
    - how long to wait before the next request is allowed
    """

    def __init__(self):
        # For each provider keep a deque of timestamps (seconds since epoch)
        # representing calls made in the last 60 seconds.
        self._calls: Dict[str, Deque[float]] = {
            provider: deque() for provider in _PROVIDER_LIMITS
        }
        self._lock = threading.Lock()

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _prune_old(self, provider: str, now: float) -> None:
        """Remove timestamps older than 60 seconds for the given provider."""
        limit_window = 60.0
        calls = self._calls[provider]
        while calls and now - calls[0] > limit_window:
            calls.popleft()

    def _current_rpm(self, provider: str, now: float) -> int:
        """Return the number of calls made in the last 60 seconds."""
        self._prune_old(provider, now)
        return len(self._calls[provider])

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def record_call(self, provider: str) -> None:
        """
        Record a request for *provider* at the current time.
        Raises KeyError if the provider is unknown.
        """
        now = time.time()
        with self._lock:
            if provider not in self._calls:
                raise KeyError(f"Unknown provider '{provider}'.")
            self._prune_old(provider, now)
            self._calls[provider].append(now)

    def utilization(self, provider: str) -> float:
        """
        Return the current utilization of the provider's minute quota as a
        fraction between 0.0 and 1.0.
        """
        now = time.time()
        with self._lock:
            if provider not in _PROVIDER_LIMITS:
                raise KeyError(f"Unknown provider '{provider}'.")
            used = self._current_rpm(provider, now)
            limit = _PROVIDER_LIMITS[provider]
            return used / limit

    def should_batch(self, provider: str) -> bool:
        """
        Return True if the provider is approaching its limit and we should
        consider batching further requests. This is true when utilization
        exceeds the configured _BATCHING_THRESHOLD.
        """
        return self.utilization(provider) >= _BATCHING_THRESHOLD

    def can_call(self, provider: str) -> bool:
        """
        Return True if a new request can be sent immediately without exceeding
        the provider's RPM limit.
        """
        now = time.time()
        with self._lock:
            if provider not in _PROVIDER_LIMITS:
                raise KeyError(f"Unknown provider '{provider}'.")
            used = self._current_rpm(provider, now)
            return used < _PROVIDER_LIMITS[provider]

    def wait_time(self, provider: str) -> float:
        """
        Return the number of seconds to wait before the next request can be
        made without breaching the limit. If a request can be made now,
        returns 0.0.
        """
        now = time.time()
        with self._lock:
            if provider not in _PROVIDER_LIMITS:
                raise KeyError(f"Unknown provider '{provider}'.")
            calls = self._calls[provider]
            self._prune_old(provider, now)

            limit = _PROVIDER_LIMITS[provider]
            if len(calls) < limit:
                return 0.0

            # The oldest call in the window determines when we drop below the limit.
            oldest = calls[0]
            # We need to wait until (oldest + 60 seconds) has passed.
            wait = (oldest + 60.0) - now
            return max(wait, 0.0)

    # -----------------------------------------------------------------------
    # Convenience: bulk recording for batched calls
    # -----------------------------------------------------------------------
    def record_batch(self, provider: str, batch_size: int) -> None:
        """
        Record *batch_size* calls that are being sent together. This simply
        records the current timestamp *batch_size* times.
        """
        now = time.time()
        with self._lock:
            if provider not in self._calls:
                raise KeyError(f"Unknown provider '{provider}'.")
            self._prune_old(provider, now)
            for _ in range(batch_size):
                self._calls[provider].append(now)

    # -----------------------------------------------------------------------
    # Debug / inspection helpers (optional, not part of core contract)
    # -----------------------------------------------------------------------
    def recent_timestamps(self, provider: str) -> List[float]:
        """
        Return a copy of the timestamps (seconds since epoch) for the last
        60 seconds. Useful for testing or logging.
        """
        now = time.time()
        with self._lock:
            self._prune_old(provider, now)
            return list(self._calls[provider])

# End of file