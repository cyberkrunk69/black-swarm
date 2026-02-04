"""
rpm_tracker.py

Utility for tracking and managing requests‑per‑minute (RPM) limits for different
LLM providers.  Currently supports:

* Groq – 30 RPM
* Together – 60 RPM

The tracker maintains a sliding‑window of timestamps for each provider and
exposes helper methods that can be used by request‑dispatch code to:

* Query current utilization (`utilization`)
* Determine if requests should be batched (`should_batch`)
* Check if an immediate call is allowed (`can_call`)
* Compute the required wait time before the next call (`wait_time`)

The implementation is lightweight, thread‑safe, and can be extended with
additional providers or custom thresholds.
"""

from __future__ import annotations

import time
import threading
from collections import deque
from typing import Deque, Dict, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
Provider = str

# Define the RPM limits for each provider
_RPM_LIMITS: Dict[Provider, int] = {
    "groq": 30,      # Groq limit: 30 requests per minute
    "together": 60,  # Together limit: 60 requests per minute
}

# Utilization threshold above which we start batching requests.
# This is a *soft* limit; the tracker will still enforce the hard RPM limit.
_BATCH_THRESHOLD = 0.80  # 80% of the provider's RPM limit


# --------------------------------------------------------------------------- #
# Core Tracker
# --------------------------------------------------------------------------- #
class RPMTracker:
    """
    Tracks request timestamps per provider using a fixed‑size sliding window
    (the last 60 seconds).  All public methods are thread‑safe.
    """

    _WINDOW_SECONDS = 60

    def __init__(self, limits: Dict[Provider, int] | None = None) -> None:
        # Allow callers to override defaults (useful for testing)
        self._limits: Dict[Provider, int] = limits or _RPM_LIMITS.copy()

        # For each provider we store a deque of timestamps (float seconds since epoch)
        self._records: Dict[Provider, Deque[float]] = {
            provider: deque() for provider in self._limits
        }

        # One lock protects all provider deques – contention is negligible given
        # the low request rates.
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _prune(self, provider: Provider) -> None:
        """
        Remove timestamps older than the sliding window for the given provider.
        Must be called with the lock held.
        """
        now = time.time()
        cutoff = now - self._WINDOW_SECONDS
        q = self._records[provider]
        while q and q[0] < cutoff:
            q.popleft()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def record_call(self, provider: Provider) -> None:
        """
        Register a new request for *provider*.  This method does not check the
        limit; callers should invoke `can_call` first if they need enforcement.
        """
        if provider not in self._limits:
            raise ValueError(f"Unknown provider: {provider!r}")

        with self._lock:
            self._prune(provider)
            self._records[provider].append(time.time())

    def utilization(self, provider: Provider) -> float:
        """
        Return the current utilization as a fraction of the provider's RPM limit.
        Value is in the range [0.0, 1.0+] (it can exceed 1.0 if the hard limit
        has already been breached).
        """
        if provider not in self._limits:
            raise ValueError(f"Unknown provider: {provider!r}")

        with self._lock:
            self._prune(provider)
            used = len(self._records[provider])
        limit = self._limits[provider]
        return used / limit

    def should_batch(self, provider: Provider) -> bool:
        """
        Return ``True`` if the current utilization exceeds the batch threshold.
        Clients can use this hint to aggregate multiple logical requests into a
        single API call (e.g., concatenating prompts).
        """
        return self.utilization(provider) >= _BATCH_THRESHOLD

    def can_call(self, provider: Provider) -> bool:
        """
        Return ``True`` if a new request can be issued without exceeding the hard
        RPM limit.  This method does **not** perform the call; it only inspects
        the current state.
        """
        if provider not in self._limits:
            raise ValueError(f"Unknown provider: {provider!r}")

        with self._lock:
            self._prune(provider)
            return len(self._records[provider]) < self._limits[provider]

    def wait_time(self, provider: Provider) -> float:
        """
        If ``can_call`` is ``False``, compute the number of seconds to wait until
        the next request would be allowed.  Returns ``0.0`` when a call can be
        made immediately.

        The calculation looks at the oldest timestamp still inside the window;
        once that timestamp ages out, the slot becomes free.
        """
        if provider not in self._limits:
            raise ValueError(f"Unknown provider: {provider!r}")

        with self._lock:
            self._prune(provider)
            q = self._records[provider]
            limit = self._limits[provider]

            if len(q) < limit:
                return 0.0

            # The next slot opens when the oldest entry exits the 60‑second window.
            oldest = q[0]
            now = time.time()
            elapsed = now - oldest
            remaining = self._WINDOW_SECONDS - elapsed
            # Guard against negative values due to timing anomalies.
            return max(0.0, remaining)

    # --------------------------------------------------------------------- #
    # Convenience static helpers (optional)
    # --------------------------------------------------------------------- #
    @staticmethod
    def default() -> "RPMTracker":
        """
        Return a singleton instance that can be shared across the application.
        """
        if not hasattr(RPMTracker, "_default_instance"):
            RPMTracker._default_instance = RPMTracker()
        return RPMTracker._default_instance


# --------------------------------------------------------------------------- #
# Example usage (not executed on import)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    tracker = RPMTracker()
    provider = "groq"

    # Simulate a few calls
    for i in range(5):
        if tracker.can_call(provider):
            tracker.record_call(provider)
            print(f"Call {i+1} recorded.")
        else:
            print(f"Call {i+1} blocked; wait {tracker.wait_time(provider):.2f}s")
        time.sleep(0.5)

    print(f"Utilization: {tracker.utilization(provider):.2%}")
    print(f"Should batch? {tracker.should_batch(provider)}")