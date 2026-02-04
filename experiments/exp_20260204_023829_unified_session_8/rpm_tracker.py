import time
import threading
from collections import deque
from typing import Deque, Tuple, Dict, Optional


class RPMTracker:
    """
    Tracks requests per minute (RPM) for multiple providers and offers helpers for
    adaptive batching and rate‑limit handling.

    Supported providers (as of this experiment):
        - "groq"     : 30 RPM limit
        - "together" : 60 RPM limit

    The tracker stores timestamps of recent calls in a sliding window (1 minute)
    and provides:
        * utilization() – current usage ratio (0.0‑1.0)
        * can_call()    – whether a new request can be sent immediately
        * wait_time()   – seconds to wait before the next request is safe
        * should_batch()– whether to batch additional items to stay under the limit
    """

    _LOCK = threading.Lock()

    # Provider → (max RPM, safety margin)
    _PROVIDER_LIMITS: Dict[str, Tuple[int, float]] = {
        "groq": (30, 0.9),      # 90 % of the hard limit to give a buffer
        "together": (60, 0.9),
    }

    def __init__(self, provider: str):
        if provider not in self._PROVIDER_LIMITS:
            raise ValueError(f"Unsupported provider '{provider}'. "
                             f"Supported: {list(self._PROVIDER_LIMITS)}")
        self.provider = provider
        self.max_rpm, self.margin = self._PROVIDER_LIMITS[provider]
        # Deque of timestamps (float seconds since epoch) for calls within the last minute
        self._calls: Deque[float] = deque()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _prune(self) -> None:
        """Remove timestamps older than 60 seconds."""
        cutoff = time.time() - 60
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()

    def _current_count(self) -> int:
        """Return number of calls made in the last 60 seconds."""
        self._prune()
        return len(self._calls)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def record_call(self) -> None:
        """
        Record a request just made. Must be called **after** a successful
        request (or a batch request) has been dispatched.
        """
        with self._LOCK:
            self._prune()
            self._calls.append(time.time())

    def utilization(self) -> float:
        """
        Return the current utilization as a float between 0.0 and 1.0,
        where 1.0 means the provider is at its (margin‑adjusted) limit.
        """
        with self._LOCK:
            count = self._current_count()
        return min(count / (self.max_rpm * self.margin), 1.0)

    def can_call(self) -> bool:
        """
        Return True if another request can be sent right now without
        exceeding the (margin‑adjusted) limit.
        """
        with self._LOCK:
            return self._current_count() < self.max_rpm * self.margin

    def wait_time(self) -> float:
        """
        Seconds to wait before the next request can be safely issued.
        Returns 0.0 if a call can be made immediately.
        """
        with self._LOCK:
            if self.can_call():
                return 0.0
            # Oldest call determines when we drop below the threshold
            oldest = self._calls[0]
            # Target count is just below the margin threshold
            target = self.max_rpm * self.margin
            # If we are over the threshold, we need to wait until enough
            # oldest entries expire.
            excess = self._current_count() - target + 1  # +1 to get under limit
            # Time when the `excess`‑th oldest entry will fall out of the window
            # (0‑based index)
            idx = int(excess) - 1
            if idx < 0:
                return 0.0
            wait_until = self._calls[idx] + 60
            return max(wait_until - time.time(), 0.0)

    def should_batch(self, batch_size: int = 1) -> bool:
        """
        Decide whether to batch additional items into the current request.

        Parameters
        ----------
        batch_size: int
            Number of additional logical requests you intend to include in the
            batch (including the one that will trigger the call).

        Returns
        -------
        bool
            True if adding `batch_size` more items keeps the projected
            utilization under the margin‑adjusted limit.
        """
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        with self._LOCK:
            projected = self._current_count() + batch_size
            return projected <= self.max_rpm * self.margin

    # --------------------------------------------------------------------- #
    # Convenience static helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def for_provider(provider: str) -> "RPMTracker":
        """Factory shortcut."""
        return RPMTracker(provider)


# ------------------------------------------------------------------------- #
# Example usage (not executed on import):
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    tracker = RPMTracker("groq")
    for i in range(5):
        if tracker.can_call():
            # pretend we send a request here
            tracker.record_call()
            print(f"Call {i+1} sent. Utilization: {tracker.utilization():.2%}")
        else:
            wt = tracker.wait_time()
            print(f"Rate limit hit, waiting {wt:.2f}s")
            time.sleep(wt)
            tracker.record_call()
            print(f"Call {i+1} sent after wait.")