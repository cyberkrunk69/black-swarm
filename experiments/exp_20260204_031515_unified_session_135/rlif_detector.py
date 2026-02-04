import re
from typing import Literal

# Simple heuristic sentiment detector.
# Returns "negative", "positive", or "neutral".
def detect_sentiment(text: str) -> Literal["negative", "positive", "neutral"]:
    """
    Detects user sentiment based on keyword heuristics.
    - Negative: frustration, angry, confused, not working, error, fail, bug
    - Positive: thanks, great, good, perfect, works, success
    Anything else is considered neutral.
    """
    text_lower = text.lower()

    negative_keywords = [
        "frustrat", "angry", "confus", "not working", "error", "fail", "bug",
        "wrong", "bad", "incorrect", "problem", "issue", "hate", "disappointed"
    ]
    positive_keywords = [
        "thanks", "thank you", "great", "good", "perfect", "works", "success",
        "nice", "awesome", "well done", "excellent"
    ]

    for kw in negative_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            return "negative"

    for kw in positive_keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
            return "positive"

    return "neutral"