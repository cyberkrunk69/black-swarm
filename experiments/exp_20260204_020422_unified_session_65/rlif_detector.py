"""
rlif_detector.py
----------------
Utility for detecting user sentiment in textual responses.

Sentiment categories:
- "positive"  – approval, satisfaction
- "negative"  – frustration, confusion, disapproval
- "neutral"   – neither clearly positive nor negative

The implementation uses simple keyword heuristics to keep the
dependency footprint minimal.  It can be swapped out later for a
more sophisticated model without changing the public API.
"""

import re
from typing import Literal

# Basic keyword lists – can be extended over time
_NEGATIVE_KEYWORDS = {
    "frustrated", "confused", "confusing", "error", "fail", "failed",
    "unable", "cannot", "can't", "won't", "bad", "incorrect", "wrong",
    "problem", "issue", "doesn't work", "does not work", "doesnt work",
    "hate", "annoyed", "annoying", "stuck", "slow", "slowly", "lag",
    "timeout", "crash", "crashed", "crashing"
}
_POSITIVE_KEYWORDS = {
    "thanks", "thank you", "great", "good", "awesome", "perfect",
    "works", "working", "nice", "well done", "appreciate", "cool",
    "excellent", "fast", "quick", "love", "liked", "like"
}


def _normalize(text: str) -> str:
    """Lower‑case and strip punctuation for simple matching."""
    return re.sub(r"[^\w\s]", "", text.lower())


def detect_sentiment(text: str) -> Literal["positive", "negative", "neutral"]:
    """
    Detect sentiment of a user message.

    Parameters
    ----------
    text: str
        The raw user response.

    Returns
    -------
    Literal["positive", "negative", "neutral"]
        Sentiment classification.
    """
    norm = _normalize(text)

    # Simple presence check – first look for negative cues
    for kw in _NEGATIVE_KEYWORDS:
        if kw in norm:
            return "negative"

    for kw in _POSITIVE_KEYWORDS:
        if kw in norm:
            return "positive"

    return "neutral"


# Simple sanity test when run directly
if __name__ == "__main__":
    samples = [
        "Thanks, that worked!",
        "I'm confused, this keeps failing.",
        "Okay."
    ]
    for s in samples:
        print(f"'{s}' -> {detect_sentiment(s)}")