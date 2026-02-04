"""
rlif_detector.py

Simple sentiment detector for Reinforcement Learning from Immediate Feedback (RLIF).
Detects three sentiment categories from a user message:
- frustration (negative)
- approval (positive)
- confusion (neutral/uncertain)

The implementation is lightweight and does not depend on external ML libraries,
making it safe to run in any environment. It uses keyword matching and basic
heuristics; more sophisticated models can be swapped in later without changing
the public API.
"""

import re
from enum import Enum
from typing import List


class Sentiment(Enum):
    FRUSTRATION = "frustration"
    APPROVAL = "approval"
    CONFUSION = "confusion"
    UNKNOWN = "unknown"


# Keywords for each sentiment. These are intentionally short and can be expanded.
_FRUSTRATION_KEYWORDS = [
    r"\b(not\s+working|failed|error|bug|issue|problem|broken|crash|hang|stuck|cannot|can't|won't|doesn't work)\b",
    r"\b(frustrated|annoyed|upset|angry|irritated)\b",
    r"\b(why\s+doesn't|why\s+won't|why\s+can't)\b",
]

_APPROVAL_KEYWORDS = [
    r"\b(good|great|thanks|thank you|awesome|perfect|works|nice|excellent|well done)\b",
    r"\b(appreciate|thankful|👍|😊|😀)\b",
]

_CONFUSION_KEYWORDS = [
    r"\b(confused|don't understand|unclear|what does|how do i|explain|unsure|not sure)\b",
    r"\b(??|\?\?)\b",
]


def _compile_patterns(keywords: List[str]) -> List[re.Pattern]:
    return [re.compile(pat, re.IGNORECASE) for pat in keywords]


_FRUSTRATION_PATTERNS = _compile_patterns(_FRUSTRATION_KEYWORDS)
_APPROVAL_PATTERNS = _compile_patterns(_APPROVAL_KEYWORDS)
_CONFUSION_PATTERNS = _compile_patterns(_CONFUSION_KEYWORDS)


def detect_sentiment(message: str) -> Sentiment:
    """
    Detect sentiment of a user message.

    Parameters
    ----------
    message : str
        The raw user message.

    Returns
    -------
    Sentiment
        One of the Sentiment enum values.
    """
    if not message:
        return Sentiment.UNKNOWN

    # Check frustration first (most critical)
    for pat in _FRUSTRATION_PATTERNS:
        if pat.search(message):
            return Sentiment.FRUSTRATION

    for pat in _APPROVAL_PATTERNS:
        if pat.search(message):
            return Sentiment.APPROVAL

    for pat in _CONFUSION_PATTERNS:
        if pat.search(message):
            return Sentiment.CONFUSION

    return Sentiment.UNKNOWN


# Simple demo when run directly
if __name__ == "__main__":
    test_cases = [
        "It doesn't work at all!",
        "Thanks, that fixed it.",
        "I'm not sure why this is happening.",
        "Just a random statement.",
    ]
    for txt in test_cases:
        print(f"Message: {txt!r} -> {detect_sentiment(txt)}")