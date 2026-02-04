"""
rlif_learner.py

A lightweight Rule‑Learning Interaction Framework (RLIF) learner.

- Extracts rules from user‑system interactions.
- Performs very simple sentiment detection on the *user* utterance.
- Positive sentiment → mild confidence boost for existing rules.
- Negative sentiment → frustration analysis + automatic rule extraction.
- Extracted rules are stored as “NEVER do X” or “ALWAYS do Y”.
"""

from __future__ import annotations
import json
import os
import re
from collections import defaultdict
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Simple sentiment heuristics ------------------------------------------------
# ----------------------------------------------------------------------
_POSITIVE_KEYWORDS = {
    "good", "great", "awesome", "nice", "thanks", "thank you", "perfect",
    "well done", "excellent", "love", "liked", "like", "fantastic"
}
_NEGATIVE_KEYWORDS = {
    "bad", "wrong", "hate", "terrible", "awful", "frustrated", "annoyed",
    "incorrect", "mistake", "error", "not helpful", "useless", "problem"
}


def _detect_sentiment(text: str) -> str:
    """
    Very naive sentiment detector.
    Returns "positive", "negative", or "neutral".
    """
    lowered = text.lower()
    pos_hits = sum(kw in lowered for kw in _POSITIVE_KEYWORDS)
    neg_hits = sum(kw in lowered for kw in _NEGATIVE_KEYWORDS)

    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


# ----------------------------------------------------------------------
# Rule handling ------------------------------------------------------------
# ----------------------------------------------------------------------
class RuleStore:
    """
    Stores extracted rules with a simple confidence score.
    Rules are strings like "NEVER do X" or "ALWAYS do Y".
    """
    def __init__(self, storage_path: str | None = None):
        self.rules: Dict[str, float] = defaultdict(float)  # rule -> confidence
        self.storage_path = storage_path
        if storage_path and os.path.exists(storage_path):
            self._load()

    def add_rule(self, rule: str, boost: float = 1.0) -> None:
        """Add a rule or increase its confidence."""
        self.rules[rule] += boost

    def boost_rule(self, rule: str, amount: float = 0.1) -> None:
        """Mild boost for a rule that already exists."""
        if rule in self.rules:
            self.rules[rule] += amount

    def get_rules(self) -> List[Tuple[str, float]]:
        """Return a list of (rule, confidence) sorted by confidence desc."""
        return sorted(self.rules.items(), key=lambda kv: kv[1], reverse=True)

    def _load(self) -> None:
        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.rules.update(data)

    def save(self) -> None:
        if not self.storage_path:
            return
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2)


# ----------------------------------------------------------------------
# Core learner --------------------------------------------------------------
# ----------------------------------------------------------------------
class RLIFLearner:
    """
    Core learner that processes a (user_input, system_response) pair.
    - Detects sentiment on the user_input.
    - Updates rule confidences or extracts new rules based on sentiment.
    """
    def __init__(self, storage_dir: str):
        os.makedirs(storage_dir, exist_ok=True)
        self.rule_store = RuleStore(storage_path=os.path.join(storage_dir, "rules.json"))

    # ------------------------------------------------------------------
    def process_interaction(self, user_input: str, system_response: str) -> None:
        """
        Main entry point.
        """
        sentiment = _detect_sentiment(user_input)
        if sentiment == "positive":
            self._handle_positive(system_response)
        elif sentiment == "negative":
            self._handle_negative(user_input, system_response)
        # neutral → nothing special

        # Persist after each interaction
        self.rule_store.save()

    # ------------------------------------------------------------------
    def _handle_positive(self, system_response: str) -> None:
        """
        Positive feedback → mild boost for any rule that matches the response.
        If no rule matches, create an "ALWAYS do ..." rule.
        """
        # Try to find an existing rule that contains the response text
        matched = False
        for rule in self.rule_store.rules:
            if system_response.lower() in rule.lower():
                self.rule_store.boost_rule(rule, amount=0.1)
                matched = True

        if not matched:
            # Create a generic positive rule
            rule = f"ALWAYS do: {system_response.strip()}"
            self.rule_store.add_rule(rule, boost=1.0)

    # ------------------------------------------------------------------
    def _handle_negative(self, user_input: str, system_response: str) -> None:
        """
        Negative feedback → extract a rule that prevents the mistake.
        Heuristics:
        - If user explicitly says "don't X" or "do not X", invert to NEVER.
        - Otherwise, create a generic NEVER rule from the system response.
        """
        # Attempt to extract a phrase after "don't"/"do not"
        neg_phrase = self._extract_negated_phrase(user_input)
        if neg_phrase:
            rule = f"NEVER do {neg_phrase}"
        else:
            # Fallback: use system response as the thing to avoid
            cleaned = system_response.strip().rstrip('.')
            rule = f"NEVER do {cleaned}"

        self.rule_store.add_rule(rule, boost=1.0)

    # ------------------------------------------------------------------
    @staticmethod
    def _extract_negated_phrase(text: str) -> str | None:
        """
        Very simple regex to find "don't X" or "do not X".
        Returns the X part or None.
        """
        pattern = re.compile(r"\b(?:don['’]?t|do not)\s+([^.,!?]+)", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
        return None

    # ------------------------------------------------------------------
    def list_rules(self) -> List[Tuple[str, float]]:
        """Convenient accessor for external callers."""
        return self.rule_store.get_rules()


# ----------------------------------------------------------------------
# Example usage (can be removed in production) ---------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simple demo when run directly
    learner = RLIFLearner(storage_dir="experiments/exp_20260204_023855_unified_session_34")
    # Simulated interactions
    learner.process_interaction(
        "Thanks, that was great!", "Here is the summary you asked for."
    )
    learner.process_interaction(
        "That didn't work, you shouldn't delete my files.", "I deleted the temporary cache."
    )
    print("Current rules:")
    for r, conf in learner.list_rules():
        print(f"{r} (confidence: {conf:.2f})")