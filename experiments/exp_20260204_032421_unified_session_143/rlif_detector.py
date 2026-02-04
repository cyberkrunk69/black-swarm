import re
from enum import Enum
from typing import Tuple

class Sentiment(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

# Simple keyword‑based sentiment detection.
_NEGATIVE_KEYWORDS = {
    "frustrated", "frustration", "angry", "mad", "hate", "bad", "wrong",
    "confused", "confusion", "unclear", "error", "failed", "fail", "problem"
}
_POSITIVE_KEYWORDS = {
    "thanks", "thank you", "good", "great", "awesome", "perfect", "nice",
    "well done", "appreciate", "approved", "correct"
}

def _normalize(text: str) -> str:
    return text.lower()

def detect_sentiment(text: str) -> Sentiment:
    """
    Very lightweight sentiment detector used by RLIF.
    Returns Sentiment.NEGATIVE if any negative keyword is present,
    Sentiment.POSITIVE if any positive keyword is present,
    otherwise Sentiment.NEUTRAL.
    """
    txt = _normalize(text)
    # Look for whole‑word matches
    for kw in _NEGATIVE_KEYWORDS:
        if re.search(rf"\\b{re.escape(kw)}\\b", txt):
            return Sentiment.NEGATIVE
    for kw in _POSITIVE_KEYWORDS:
        if re.search(rf"\\b{re.escape(kw)}\\b", txt):
            return Sentiment.POSITIVE
    return Sentiment.NEUTRAL