"""
hedging_detector.py
-------------------

A lightweight hedging‑detector that uses pattern matching to flag statements
that contain linguistic hedges (e.g., “maybe”, “might”, “I think”, “could be”).
The detector is designed to be used with the ``self_observer`` framework for
real‑time observation of generated text.

The implementation focuses on:
* A curated list of hedge patterns (regex based, case‑insensitive).
* A ``detect`` method returning ``True`` when any hedge is found.
* Integration hook for ``self_observer`` – the detector registers a callback
  that receives each new text fragment and logs a detection event.

The detector is deliberately simple to keep the false‑positive rate low.
Further tuning (e.g., contextual analysis) can be added later.
"""

import re
import logging
from typing import List, Pattern

# Attempt to import the self_observer infrastructure.
# If it is unavailable (e.g., during isolated unit tests), we fall back to a
# no‑op stub so the module remains importable.
try:
    from self_observer import register_observer, ObservationEvent
except Exception:  # pragma: no cover
    def register_observer(callback):
        # No‑op stub for environments without self_observer.
        return

    class ObservationEvent:
        """Minimal stub used only for type hinting."""
        def __init__(self, text: str):
            self.text = text


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class HedgingDetector:
    """
    Detects hedging language in a given text fragment.

    Example
    -------
    >>> detector = HedgingDetector()
    >>> detector.detect("I think this might work.")
    True
    >>> detector.detect("The algorithm converges in O(n) time.")
    False
    """

    # Common hedging phrases – the list can be extended.
    _hedge_phrases: List[str] = [
        r"\bmaybe\b",
        r"\bperhaps\b",
        r"\bpossibly\b",
        r"\bpossibility\b",
        r"\bmight\b",
        r"\bcould be\b",
        r"\bI think\b",
        r"\bI believe\b",
        r"\bit seems\b",
        r"\bappears to be\b",
        r"\blikely\b",
        r"\bprobably\b",
        r"\bseems?\b",
        r"\buncertain\b",
        r"\bnot sure\b",
        r"\bguess\b",
        r"\bpossible\b",
        r"\bpotentially\b",
        r"\bmay be\b",
        r"\bmaybe\b",
    ]

    def __init__(self, additional_patterns: List[str] = None):
        """
        Initialise the detector.

        Parameters
        ----------
        additional_patterns : list of str, optional
            Extra regex patterns to consider as hedges.
        """
        pattern_strings = self._hedge_phrases + (additional_patterns or [])
        # Compile a single regex that matches any hedge phrase.
        self._regex: Pattern = re.compile(
            "|".join(pattern_strings), flags=re.IGNORECASE
        )
        logger.debug("HedgingDetector compiled regex: %s", self._regex.pattern)

        # Register with self_observer for real‑time detection if possible.
        try:
            register_observer(self._observer_callback)
            logger.debug("HedgingDetector registered with self_observer.")
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to register with self_observer: %s", exc)

    def detect(self, text: str) -> bool:
        """
        Return ``True`` if the supplied text contains any hedging phrase.

        Parameters
        ----------
        text : str
            The text to analyse.

        Returns
        -------
        bool
            ``True`` if a hedge is detected, ``False`` otherwise.
        """
        if not text:
            return False
        match = self._regex.search(text)
        if match:
            logger.debug("Hedging detected: %s (matched \"%s\")", text, match.group())
            return True
        logger.debug("No hedging detected in: %s", text)
        return False

    # --------------------------------------------------------------------- #
    # self_observer integration
    # --------------------------------------------------------------------- #
    def _observer_callback(self, event: ObservationEvent):
        """
        Callback invoked by ``self_observer`` for each observed text fragment.

        Parameters
        ----------
        event : ObservationEvent
            The observation containing the text to analyse.
        """
        if self.detect(event.text):
            # In a real system we might emit a structured event; here we just log.
            logger.info("Hedging detected in observed text: %s", event.text)


# Convenience singleton for modules that prefer a ready‑made detector.
default_detector = HedgingDetector()