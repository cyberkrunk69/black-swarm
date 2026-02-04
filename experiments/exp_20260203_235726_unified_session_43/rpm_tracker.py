\"\"\"rpm_tracker.py
Utility for tracking and managing requests‑per‑minute (RPM) limits for different LLM providers.

Supported providers (and their limits):
- Groq:      30 RPM
- Together:  60 RPM

The :class:`RPMTracker` class records timestamps of each request, computes current
utilization, determines whether a new call can be made, suggests adaptive
batching, and calculates the required wait time when a limit is reached.

Typical usage::

    from rpm_tracker import RPMTracker

    rpm = RPMTracker()
    if rpm.can_call('groq'):
        # make request
        rpm.record_call('groq')
    else:
        time.sleep(rpm.wait_time('groq'))

The implementation is thread‑safe and lightweight, suitable for inclusion in
any codebase that needs to respect provider rate limits.
\"\"\"

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque, Dict


class RPMTracker:
    \"\"\"Track RPM usage per provider and offer helper methods.

    The tracker keeps a sliding window of timestamps (seconds since epoch) for
    each provider.  All calculations are performed over the last 60 seconds.
    \"\"\"

    # Provider‑specific RPM limits
    _LIMITS: Dict[str, int] = {
        "groq": 30,      # Groq limit: 30 requests per minute
        "together": 60,  # Together limit: 60 requests per minute
    }

    # Utilization threshold at which we start recommending batching
    _BATCH_THRESHOLD: float = 0.80  # 80 % of the limit

    def __init__(self) -> None:
        # Deques store timestamps (float) in ascending order.
        self._timestamps: Dict[str, Deque[float]] = {
            provider: deque() for provider in self._LIMITS
        }
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _now(self) -> float:
        return time.time()

    def _prune(self, provider: str) -> None:
        \"\"\"Remove timestamps older than 60 seconds for *provider*.

        This method assumes the lock is already held.
        \"\"\"
        cutoff = self._now() - 60
        dq = self._timestamps[provider]
        while dq and dq[0] < cutoff:
            dq.popleft()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def record_call(self, provider: str) -> None:
        \"\"\"Record a request for *provider* at the current time.

        Raises:
            KeyError: If *provider* is unknown.
        """
        if provider not in self._LIMITS:
            raise KeyError(f"Unsupported provider: {provider}")

        with self._lock:
            self._prune(provider)
            self._timestamps[provider].append(self._now())

    def utilization(self, provider: str) -> float:
        \"\"\"Return the current utilization ratio (0.0 – 1.0) for *provider*.

        The ratio is ``current_calls / limit`` where *current_calls* is the
        number of requests made in the last 60 seconds.
        """
        if provider not in self._LIMITS:
            raise KeyError(f"Unsupported provider: {provider}")

        with self._lock:
            self._prune(provider)
            current = len(self._timestamps[provider])
        return current / self._LIMITS[provider]

    def can_call(self, provider: str) -> bool:
        \"\"\"Return ``True`` if a new request can be made without exceeding the limit.

        The check is performed against the sliding 60‑second window.
        """
        return self.utilization(provider) < 1.0

    def wait_time(self, provider: str) -> float:
        \"\"\"Return seconds to wait before the next request can be made.

        If the provider is currently under the limit, ``0.0`` is returned.
        """
        if provider not in self._LIMITS:
            raise KeyError(f"Unsupported provider: {provider}")

        with self._lock:
            self._prune(provider)
            dq = self._timestamps[provider]
            if len(dq) < self._LIMITS[provider]:
                return 0.0
            # The oldest request determines when we drop back under the limit.
            oldest = dq[0]
        elapsed = self._now() - oldest
        # We need to wait until the oldest request is >60 seconds old.
        return max(0.0, 60.0 - elapsed)

    def should_batch(self, provider: str) -> bool:
        \"\"\"Suggest whether to batch requests for *provider*.

        Returns ``True`` when utilization exceeds the configured batch threshold
        (default 80 %).  Consumers can use this hint to combine multiple logical
        requests into a single API call, reducing the number of round‑trips.
        """
        return self.utilization(provider) >= self._BATCH_THRESHOLD

    # --------------------------------------------------------------------- #
    # Convenience utilities
    # --------------------------------------------------------------------- #
    def reset(self, provider: str | None = None) -> None:
        \"\"\"Clear all stored timestamps.

        If *provider* is ``None`` (default), all providers are cleared.
        """
        with self._lock:
            if provider is None:
                for dq in self._timestamps.values():
                    dq.clear()
            else:
                if provider not in self._LIMITS:
                    raise KeyError(f"Unsupported provider: {provider}")
                self._timestamps[provider].clear()

    # --------------------------------------------------------------------- #
    # Representation helpers
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:
        with self._lock:
            parts = [
                f"{p}: {len(dq)}/{self._LIMITS[p]} ({self.utilization(p):.2%})"
                for p, dq in self._timestamps.items()
            ]
        return f"<RPMTracker {' | '.join(parts)}>"