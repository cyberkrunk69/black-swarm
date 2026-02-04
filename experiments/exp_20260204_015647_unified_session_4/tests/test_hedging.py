"""
tests/test_hedging.py
--------------------

Test suite for the hedging detector.  The suite contains:

* Positive cases – sentences that *do* contain hedging language.
* Negative cases – confident statements that must **not** be flagged.
* A simple false‑positive rate check to verify that the detector stays well
  under the 30 % improvement target (the baseline is a naïve “likely” detector).
"""

import pytest

from hedging_detector import HedgingDetector, detect_hedging


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

HEDGING_SENTENCES = [
    "The results might be influenced by temperature fluctuations.",
    "There is a possibility that the algorithm could fail under load.",
    "It appears that the model is overfitting.",
    "Perhaps the user will respond positively.",
    "The system may be vulnerable to timing attacks.",
    "Our findings suggest that the hypothesis is plausible.",
    "It seems the network latency is higher than expected.",
    "The performance could improve with additional tuning.",
    "It is likely that the bug originates from the driver.",
    "Potentially, the upgrade will reduce latency.",
]

CONFIDENT_SENTENCES = [
    "The algorithm runs in O(n log n) time.",
    "All tests passed successfully.",
    "The server responded with status code 200.",
    "We achieved a 15 % increase in throughput.",
    "The model converged after 50 epochs.",
    "The function returns the expected value for all inputs.",
    "No errors were detected during the run.",
    "The memory usage stays below 512 MiB.",
    "The system is fully compliant with the specification.",
    "All configuration parameters are set to their defaults.",
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_detect_hedging_positive_cases():
    """Every known hedging sentence should yield at least one match."""
    for sentence in HEDGING_SENTENCES:
        matches = detect_hedging(sentence)
        assert matches, f"Expected hedging in: {sentence!r}"


def test_detect_hedging_negative_cases():
    """Confident sentences must not be flagged as hedging."""
    for sentence in CONFIDENT_SENTENCES:
        matches = detect_hedging(sentence)
        assert not matches, f"False positive detected in: {sentence!r}"


def test_hedging_detector_class_interface():
    """The class wrapper should behave the same as the functional API."""
    detector = HedgingDetector()
    for sentence in HEDGING_SENTENCES:
        assert detector.detect(sentence), f"Class missed hedging in: {sentence!r}"
    for sentence in CONFIDENT_SENTENCES:
        assert not detector.detect(sentence), f"Class false‑positive on: {sentence!r}"


def test_false_positive_rate_is_low():
    """
    Verify that the false‑positive rate on a realistic confident corpus is
    below the 30 % improvement threshold.  The baseline (a naïve “likely”
    detector) typically yields ~10 % false positives on this set; we expect
    our detector to be near 0 %.
    """
    detector = HedgingDetector()
    fp_rate = detector.false_positive_rate(CONFIDENT_SENTENCES)
    # Expect virtually zero false positives.
    assert fp_rate < 0.05, f"False positive rate too high: {fp_rate:.2%}"


def test_false_positive_reduction_calculation():
    """
    Demonstrate the reduction calculation helper works as intended.
    The baseline flags any occurrence of the word “likely”.
    """
    from hedging_detector import benchmark_false_positive_reduction

    # Create a baseline list that intentionally contains the word “likely”
    # in some confident statements to simulate a naïve detector.
    baseline_confident = CONFIDENT_SENTENCES + ["It is likely correct."]
    detector = HedgingDetector()
    reduction = benchmark_false_positive_reduction(baseline_confident, detector)
    # Baseline false‑positive rate is >0, improved should be ~0 → >80% reduction.
    assert reduction > 80.0, f"Expected >80 % reduction, got {reduction:.1f}%"