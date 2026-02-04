"""
tests/test_hedging.py
--------------------

Unit tests for the ``hedging_detector`` module. The suite contains examples of
hedging statements (expected to be flagged) and confident statements (expected
to be ignored). The false‑positive rate can be measured by running the tests
and ensuring all confident statements pass without detection.
"""

import pytest

from ..hedging_detector import HedgingDetector, default_detector


# --------------------------------------------------------------------- #
# Test data
# --------------------------------------------------------------------- #

# Statements that contain hedging language – should be detected.
HEDGING_STATEMENTS = [
    "I think this might work.",
    "Perhaps we should reconsider the approach.",
    "It could be that the model is overfitting.",
    "Maybe the results are due to random chance.",
    "There is a possibility that the algorithm diverges.",
    "It seems the data is noisy.",
    "I'm not sure if this is correct.",
    "Potentially, the system could fail under load.",
    "It appears to be a minor issue.",
    "Probably the best we can do.",
]

# Statements that are confident/assertive – should NOT be detected.
CONFIDENT_STATEMENTS = [
    "The algorithm converges in O(n) time.",
    "We achieved 99.5% accuracy on the test set.",
    "The model predicts the next token with high confidence.",
    "All experiments were replicated successfully.",
    "The loss decreased monotonically over 100 epochs.",
    "Our method outperforms the baseline by 12%.",
    "The system processes 10k requests per second.",
    "We proved the theorem using induction.",
    "The code runs without errors on Linux.",
    "The architecture scales linearly with the number of nodes.",
]


# --------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("text", HEDGING_STATEMENTS)
def test_hedging_detected(text):
    """Every known hedging statement should be flagged."""
    assert default_detector.detect(text) is True, f"Failed to detect hedge in: {text}"


@pytest.mark.parametrize("text", CONFIDENT_STATEMENTS)
def test_confident_not_detected(text):
    """Confident statements must not trigger a false positive."""
    assert default_detector.detect(text) is False, f"False positive on: {text}"


def test_custom_detector_with_extra_pattern():
    """Validate that additional user‑provided patterns are respected."""
    extra = [r"\bdefinitely\b"]
    detector = HedgingDetector(additional_patterns=extra)

    assert detector.detect("We will definitely succeed.") is True
    assert detector.detect("We will succeed.") is False