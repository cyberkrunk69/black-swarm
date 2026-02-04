"""hedging_detector.py
A lightweight hedging‑detector that integrates with the project's ``self_observer`` framework.

The detector looks for common hedging constructions (e.g. “might”, “could be”, “possibly”, “I think”, “maybe”)
and returns the matched spans.  It is deliberately simple – the goal of the benchmark is to
measure false‑positive reduction when the detector is used in real‑time via the observer.

The public API:
    - HedgingDetector(patterns=None): optional custom regex patterns.
    - detect(text: str) -> List[Tuple[str, int, int]]: returns a list of (match, start, end).
    - register_observer(): registers a callback with ``self_observer`` that runs detection on each
      incoming message and stores the result in ``self_observer.latest_hedging``.
"""

import re
from typing import List, Tuple, Pattern, Optional

# Attempt to import the self_observer infrastructure.  If it does not exist (e.g. when the
# module is run in isolation) we fall back to a no‑op stub so that the file can still be
# imported without side effects.
try:
    import self_observer  # type: ignore
except Exception:  # pragma: no cover
    class _NoOpObserver:
        latest_hedging = None

        @staticmethod
        def register_callback(_):
            pass

    self_observer = _NoOpObserver()  # type: ignore


DEFAULT_PATTERNS = [
    r"\bmaybe\b",
    r"\bperhaps\b",
    r"\bpossibly\b",
    r"\bmight\b",
    r"\bcould be\b",
    r"\bI think\b",
    r"\bI believe\b",
    r"\bseems? (to be)?\b",
    r"\bappears? (to be)?\b",
    r"\blikely\b",
    r"\bunlikely\b",
    r"\bprobable\b",
    r"\bprobable\b",
    r"\bpotentially\b",
    r"\bas far as I know\b",
    r"\bto the best of my knowledge\b",
]


class HedgingDetector:
    """Detect hedging language in a piece of text."""

    def __init__(self, patterns: Optional[List[str]] = None):
        """
        Initialise the detector.

        Args:
            patterns: Optional list of regex strings. If omitted, the default hedging patterns
                      are used. Patterns are compiled with ``re.IGNORECASE``.
        """
        pattern_strings = patterns if patterns is not None else DEFAULT_PATTERNS
        # Compile each pattern once for performance.
        self._regexes: List[Pattern] = [
            re.compile(p, flags=re.IGNORECASE) for p in pattern_strings
        ]

    def detect(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Scan *text* for hedging phrases.

        Returns:
            A list of tuples ``(match_text, start_index, end_index)`` for each
            detected hedging phrase. Overlapping matches are merged by taking the earliest
            start and latest end for the same phrase.
        """
        matches: List[Tuple[str, int, int]] = []
        for regex in self._regexes:
            for m in regex.finditer(text):
                matches.append((m.group(0), m.start(), m.end()))
        # Optional simple deduplication (identical spans)
        uniq = {}
        for phrase, start, end in matches:
            key = (start, end)
            if key not in uniq:
                uniq[key] = phrase
        return [(uniq[k], k[0], k[1]) for k in sorted(uniq)]

    # --------------------------------------------------------------------- #
    # Integration with the self_observer framework
    # --------------------------------------------------------------------- #
    def _observer_callback(self, message: str) -> None:
        """
        Callback invoked by the self_observer when a new message arrives.
        The result is stored on ``self_observer.latest_hedging`` for downstream
        components.
        """
        self_observer.latest_hedging = self.detect(message)

    def register_observer(self) -> None:
        """
        Register the detector with the global ``self_observer``.  The observer is
        expected to expose a ``register_callback(callable)`` method.
        """
        if hasattr(self_observer, "register_callback"):
            self_observer.register_callback(self._observer_callback)


# ------------------------------------------------------------------------- #
# Convenience singleton for the rest of the code base
# ------------------------------------------------------------------------- #
default_detector = HedgingDetector()
default_detector.register_observer()