import re
from typing import Literal, Tuple

Sentiment = Literal["positive", "negative", "neutral"]


_NEGATIVE_KEYWORDS = {
    "frustration": [
        r"\b(?:fail|error|cannot|can't|won't|unable|problem|issue|bug|crash|confused|confusing|bad|wrong|mistake)\b",
        r"\b(?:frustrated|annoyed|upset|angry)\b",
    ],
    "confusion": [
        r"\b(?:don'?t understand|confused|confusing|unclear|uncertainty|unsure)\b",
    ],
    "approval": [
        r"\b(?:thanks|thank you|great|good|perfect|awesome|nice|well done)\b",
    ],
}


def _contains_pattern(text: str, patterns: list[str]) -> bool:
    """Return True if any regex pattern matches the text (case‑insensitive)."""
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False


def detect_sentiment(user_response: str) -> Sentiment:
    """
    Very lightweight sentiment detector focused on the three categories required by RLIF:
    - positive (approval)
    - negative (frustration or confusion)
    - neutral (none of the above)

    The function looks for keyword patterns; it is deliberately simple to keep runtime
    overhead low and avoid external model calls.
    """
    lowered = user_response.lower()

    # Positive sentiment has priority – if user thanks us we consider it positive.
    if _contains_pattern(lowered, _NEGATIVE_KEYWORDS["approval"]):
        return "positive"

    # Any frustration or confusion keyword => negative.
    if _contains_pattern(lowered, _NEGATIVE_KEYWORDS["frustration"] + _NEGATIVE_KEYWORDS["confusion"]):
        return "negative"

    return "neutral"


def sentiment_summary(user_response: str) -> Tuple[Sentiment, str]:
    """
    Returns a tuple of (sentiment, reason). The reason is a short description
    of why the sentiment was classified that way – useful for logging.
    """
    sentiment = detect_sentiment(user_response)
    if sentiment == "positive":
        reason = "User expressed approval or gratitude."
    elif sentiment == "negative":
        reason = "User expressed frustration, confusion, or reported an error."
    else:
        reason = "No clear sentiment detected."
    return sentiment, reason