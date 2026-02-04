"""
hedging_detector.py
-------------------

A lightweight hedging detection module that uses pattern‑matching to identify
linguistic hedges (e.g., “might”, “possibly”, “appears to”).  The detector is
designed to be used together with the project's ``self_observer`` infrastructure
for real‑time observation of detection events.

The implementation focuses on:
* A curated list of common hedging expressions.
* Efficient compiled regular‑expression matching.
* An easy‑to‑use ``HedgingDetector`` class.
* Minimal false‑positive behaviour – the pattern list is deliberately scoped
  to avoid overly generic terms.

The module also provides a small utility to compute the false‑positive rate
given a collection of known confident statements.
"""

import re
import logging
from typing import List, Tuple

# Optional import – the self_observer package is part of the broader system.
# If it is unavailable (e.g., during isolated unit testing) we fall back to a
# no‑op stub so that the detector remains importable.
try:
    from self_observer import observe  # type: ignore
except Exception:  # pragma: no cover
    def observe(event: str, data: dict):
        """Fallback stub for ``self_observer.observe`` when the real package is missing."""
        logging.debug(f"[self_observer stub] Event: {event}, Data: {data}")

# ---------------------------------------------------------------------------
# Hedging patterns
# ---------------------------------------------------------------------------

# The list intentionally avoids overly generic words (e.g., “likely” can be
# ambiguous) and focuses on phrases that are strong indicators of uncertainty.
_HEDGING_PHRASES = [
    r"\bmay be\b",
    r"\bmight be\b",
    r"\bcould be\b",
    r"\bpossibly\b",
    r"\bperhaps\b",
    r"\bmaybe\b",
    r"\bappears to be\b",
    r"\bseems to be\b",
    r"\bappears\b",
    r"\bseems\b",
    r"\blikely\b",
    r"\bpotentially\b",
    r"\bprobable\b",
    r"\bprobable that\b",
    r"\bmay\b",
    r"\bcould\b",
    r"\bsuggests?\b",
    r"\bindicates?\b",
    r"\bimplies?\b",
]

# Compile a single regex that matches any of the hedging phrases, case‑insensitive.
_HEDGING_REGEX = re.compile("|".join(_HEDGING_PHRASES), flags=re.IGNORECASE)


def detect_hedging(text: str) -> List[Tuple[str, int, int]]:
    """
    Scan *text* for hedging expressions.

    Returns
    -------
    List[Tuple[str, int, int]]
        A list of tuples ``(match_text, start_index, end_index)`` for each
        hedging phrase found.
    """
    matches = []
    for match in _HEDGING_REGEX.finditer(text):
        matches.append((match.group(0), match.start(), match.end()))
    return matches


class HedgingDetector:
    """
    High‑level detector that integrates with the ``self_observer`` system.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def detect(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detect hedging in *text* and emit an observation event.

        Parameters
        ----------
        text : str
            Input sentence or paragraph.

        Returns
        -------
        List[Tuple[str, int, int]]
            Detected hedging spans.
        """
        hedges = detect_hedging(text)
        if hedges:
            # Emit a real‑time observation for downstream tooling.
            observe(
                event="hedging_detected",
                data={"text": text, "matches": [m[0] for m in hedges]},
            )
            self.logger.debug(f"Hedging detected: {hedges}")
        else:
            observe(event="hedging_not_detected", data={"text": text})
            self.logger.debug("No hedging detected.")
        return hedges

    @staticmethod
    def false_positive_rate(confident_texts: List[str]) -> float:
        """
        Compute the false‑positive rate over a collection of *confident_texts*.

        The rate is defined as::

            FP / (FP + TN)

        where *FP* is the number of confident statements incorrectly flagged as
        hedging and *TN* is the number of confident statements correctly ignored.

        Parameters
        ----------
        confident_texts : List[str]
            Sentences that are known *not* to contain hedging.

        Returns
        -------
        float
            False‑positive rate in the range [0.0, 1.0].
        """
        false_positives = sum(1 for txt in confident_texts if detect_hedging(txt))
        total = len(confident_texts)
        if total == 0:
            return 0.0
        return false_positives / total


# ---------------------------------------------------------------------------
# Simple benchmark helper (used by the test suite)
# ---------------------------------------------------------------------------

def benchmark_false_positive_reduction(
    baseline_texts: List[str],
    improved_detector: "HedgingDetector",
) -> float:
    """
    Compare the false‑positive rate of the current detector against a baseline
    (the original heuristic that simply flagged any occurrence of the word
    “likely”).  The function returns the percentage reduction.

    This helper is **not** part of the public API; it exists solely for the
    experiment's benchmark script.
    """
    # Baseline: flag any occurrence of the word "likely" (case‑insensitive)
    baseline_fp = sum(1 for txt in baseline_texts if re.search(r"\blikely\b", txt, re.I))
    baseline_rate = baseline_fp / len(baseline_texts) if baseline_texts else 0.0

    improved_rate = improved_detector.false_positive_rate(baseline_texts)

    if baseline_rate == 0:
        return 0.0
    reduction = (baseline_rate - improved_rate) / baseline_rate * 100.0
    return reduction