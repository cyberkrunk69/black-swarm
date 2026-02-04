"""
rpm_tracker.py

Utility for tracking and managing per‑minute request rates (RPM) for external LLM providers.
Current providers:
* Groq   – 30 RPM limit
* Together – 60 RPM limit

The tracker records timestamps of each request, computes utilization, and offers helpers
for adaptive batching and throttling:

* utilization(provider) → float
* should_batch(provider, threshold=0.8) → bool
* can_call(provider) → bool
* wait_time(provider) → float (seconds until a new call is allowed)

The implementation is deliberately lightweight, thread‑safe, and has no external
dependencies beyond the Python standard library.
"""

from __future__ import annotations

import collections
import threading
import time
from typing import Deque, Dict, List


class RPMTracker:
    """
    Tracks requests per minute for each provider and provides helpers for adaptive
    batching and throttling.
    """

    # Provider‑specific RPM limits
    _LIMITS: Dict[str, int] = {
        "groq": 30,      # Groq limit: 30 requests per minute
        "together": 60,  # Together limit: 60 requests per minute
    }

    def __init__(self, window_seconds: int = 60) -> None:
        """
        Initialise the tracker.

        Args:
            window_seconds: Length of the sliding window for RPM calculation.
                            Default is 60 seconds (one minute).
        """
        self._window = window_seconds
        # Mapping provider -> deque of request timestamps (float seconds since epoch)
        self._records: Dict[str, Deque[float]] = {
            provider: collections.deque() for provider in self._LIMITS
        }
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _prune(self, provider: str) -> None:
        """Remove timestamps older than the current sliding window."""
        cutoff = time.time() - self._window
        q = self._records[provider]
        while q and q[0] < cutoff:
            q.popleft()

    def _record(self, provider: str) -> None:
        """Record a new request timestamp for *provider*."""
        self._records[provider].append(time.time())

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def record_call(self, provider: str) -> None:
        """
        Public entry point to log a request.  The method is thread‑safe.

        Raises:
            ValueError: If the provider is unknown.
        """
        provider = provider.lower()
        if provider not in self._LIMITS:
            raise ValueError(f"Unsupported provider '{provider}'. Available: {list(self._LIMITS)}")
        with self._lock:
            self._prune(provider)
            self._record(provider)

    def utilization(self, provider: str) -> float:
        """
        Return the current utilization ratio (0.0 – 1.0) for *provider*.

        Utilization = (requests in last minute) / (RPM limit)

        Returns:
            float: Utilization ratio; 0.0 if no recent requests.
        """
        provider = provider.lower()
        if provider not in self._LIMITS:
            raise ValueError(f"Unsupported provider '{provider}'.")
        with self._lock:
            self._prune(provider)
            current = len(self._records[provider])
        return current / self._LIMITS[provider]

    def should_batch(self, provider: str, threshold: float = 0.8) -> bool:
        """
        Determine whether incoming requests should be batched for *provider*.

        Batching is recommended when utilization exceeds *threshold* (default 80%).
        """
        return self.utilization(provider) >= threshold

    def can_call(self, provider: str) -> bool:
        """
        Return ``True`` if a new request can be issued without exceeding the RPM limit.
        """
        return self.utilization(provider) < 1.0

    def wait_time(self, provider: str) -> float:
        """
        Compute the number of seconds to wait before the next request can be made
        without violating the RPM limit.  Returns 0.0 if a call can be made immediately.

        The calculation looks at the oldest request still inside the sliding window.
        """
        provider = provider.lower()
        if provider not in self._LIMITS:
            raise ValueError(f"Unsupported provider '{provider}'.")
        with self._lock:
            self._prune(provider)
            q = self._records[provider]
            if len(q) < self._LIMITS[provider]:
                return 0.0
            # The next slot opens when the oldest timestamp exits the window
            oldest_timestamp = q[0]
        elapsed = time.time() - oldest_timestamp
        remaining = self._window - elapsed
        return max(0.0, remaining)

    # --------------------------------------------------------------------- #
    # Convenience helpers for typical usage patterns
    # --------------------------------------------------------------------- #
    def maybe_wait(self, provider: str) -> None:
        """
        If the provider is at its limit, sleep for the required wait time.
        """
        delay = self.wait_time(provider)
        if delay > 0:
            time.sleep(delay)

    def reset(self) -> None:
        """
        Clear all recorded timestamps (useful for testing).
        """
        with self._lock:
            for q in self._records.values():
                q.clear()


# ------------------------------------------------------------------------- #
# Example usage (removed in production, kept for reference)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    tracker = RPMTracker()
    prov = "groq"

    # Simulate a burst of 30 calls
    for _ in range(30):
        tracker.record_call(prov)

    print(f"Utilization for {prov}: {tracker.utilization(prov):.2%}")
    print(f"Can call now? {tracker.can_call(prov)}")
    print(f"Should batch? {tracker.should_batch(prov)}")
    print(f"Wait time (s): {tracker.wait_time(prov):.2f}")