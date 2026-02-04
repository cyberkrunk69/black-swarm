"""
Integration helpers for the RLIF subsystem.

The core engine (grind_spawner_unified.py) should import this module and invoke
`process_interaction` after each user‑assistant exchange.

Because core files are marked READ‑ONLY, this file provides a non‑intrusive hook
that can be called from the existing codebase without modifying it.
"""

from typing import Dict, Any

from .rlif_detector import detect_sentiment, sentiment_summary
from .rlif_analyzer import analyze_failure
from .rlif_rules import store_rule, get_applicable_rules


def process_interaction(
    user_prompt: str,
    assistant_response: str,
    user_feedback: str,
) -> Dict[str, Any]:
    """
    Called after the assistant has responded and the user has given feedback.
    It performs the RLIF workflow:

    1. Detect sentiment.
    2. If negative → run analyzer, extract rule, store it.
    3. Return any applicable rules for the next turn (so the caller can prepend them).

    Returns a dictionary containing:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "reason": str,
            "new_rule": Optional[str],
            "applicable_rules": List[str],
        }
    """
    sentiment, reason = sentiment_summary(user_feedback)

    new_rule = None
    if sentiment == "negative":
        analysis = analyze_failure(user_prompt, assistant_response, user_feedback)
        store_rule(analysis)
        new_rule = analysis

    # Gather rules that might be relevant to the upcoming prompt.
    applicable = get_applicable_rules(user_prompt)

    return {
        "sentiment": sentiment,
        "reason": reason,
        "new_rule": new_rule,
        "applicable_rules": applicable,
    }