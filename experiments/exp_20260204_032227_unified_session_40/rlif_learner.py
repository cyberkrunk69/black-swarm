"""
rlif_learner.py
----------------
A lightweight Rule‑Learning Interaction Framework (RLIF) learner that:

* Receives a user utterance and the system's response.
* Performs a very simple sentiment analysis on the **system response**.
* If sentiment is positive → applies a mild “confidence boost”.
* If sentiment is negative → performs a basic “frustration analysis”, extracts
  actionable information from the interaction and synthesises rule statements.
* Rules are expressed in an inverted‑mistake format:
      - “NEVER do X”  – what caused frustration.
      - “ALWAYS do Y” – what appeared to satisfy the user.

The implementation purposefully avoids heavy NLP dependencies to keep the
experiment lightweight and fast.  It can be swapped out for a more sophisticated
sentiment model later without changing the public API.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple


# --------------------------------------------------------------------------- #
# Simple sentiment utilities
# --------------------------------------------------------------------------- #

_POSITIVE_WORDS = {
    "good", "great", "excellent", "awesome", "nice", "perfect",
    "thanks", "thank", "thankyou", "thank you", "love", "liked",
    "happy", "pleased", "satisfied", "well done", "fantastic"
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "hate", "hated", "horrible",
    "wrong", "incorrect", "mistake", "error", "fail", "failed",
    "frustrated", "annoyed", "unhappy", "disappointed", "not good",
    "not helpful", "useless", "problem", "issue", "cannot", "can't"
}


def _normalize(text: str) -> List[str]:
    """Lower‑case, strip punctuation and split into words."""
    translator = str.maketrans("", "", string.punctuation)
    return text.lower().translate(translator).split()


def simple_sentiment_score(text: str) -> int:
    """
    Very naive sentiment scoring:
        +1 for each positive word
        -1 for each negative word
    Returns an integer that can be positive, zero or negative.
    """
    tokens = _normalize(text)
    pos = sum(tok in _POSITIVE_WORDS for tok in tokens)
    neg = sum(tok in _NEGATIVE_WORDS for tok in tokens)
    return pos - neg


# --------------------------------------------------------------------------- #
# Rule extraction helpers
# --------------------------------------------------------------------------- #

def _extract_keywords(text: str, max_keywords: int = 3) -> List[str]:
    """
    Extract up to `max_keywords` most frequent non‑stop words.
    This is a placeholder for a more advanced keyword extractor.
    """
    # Very small stop‑word list; expand as needed.
    STOP_WORDS = {
        "the", "a", "an", "i", "you", "we", "they", "it", "is", "are",
        "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "and", "or", "but", "if", "then", "so",
        "to", "of", "in", "for", "on", "with", "at", "by", "from"
    }

    tokens = [tok for tok in _normalize(text) if tok not in STOP_WORDS]
    most_common = Counter(tokens).most_common(max_keywords)
    return [word for word, _ in most_common]


def _format_rule(prefix: str, keywords: List[str]) -> str:
    """
    Turn a list of keywords into a human‑readable rule.
    Example: prefix="NEVER", keywords=["delete", "file"] → "NEVER delete file"
    """
    if not keywords:
        return f"{prefix} <unspecified>"
    return f"{prefix} " + " ".join(keywords)


# --------------------------------------------------------------------------- #
# Core learner implementation
# --------------------------------------------------------------------------- #

@dataclass
class RLIFLearner:
    """
    Rule‑Learning Interaction Framework learner.

    Attributes
    ----------
    confidence : float
        A simple numeric confidence that is mildly increased on positive
        sentiment and decreased on negative sentiment.
    extracted_rules : List[str]
        Accumulated rules generated from negative interactions.
    """
    confidence: float = 0.5
    extracted_rules: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def process_interaction(self, user_input: str, system_response: str) -> Tuple[float, List[str]]:
        """
        Process a single interaction.

        Parameters
        ----------
        user_input : str
            What the user said / typed.
        system_response : str
            The system's reply to the user.

        Returns
        -------
        Tuple[float, List[str]]
            Updated confidence and any newly generated rules (empty list if none).
        """
        sentiment = simple_sentiment_score(system_response)

        if sentiment > 0:
            self._apply_positive_boost()
            # No rule extraction on positive feedback.
            return self.confidence, []

        # sentiment <= 0 → treat as frustration / negative feedback
        self._apply_negative_penalty()
        new_rules = self._extract_rules_from_interaction(user_input, system_response)
        self.extracted_rules.extend(new_rules)
        return self.confidence, new_rules

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #

    def _apply_positive_boost(self) -> None:
        """Mildly increase confidence (capped at 1.0)."""
        self.confidence = min(1.0, self.confidence + 0.05)

    def _apply_negative_penalty(self) -> None:
        """Mildly decrease confidence (floored at 0.0)."""
        self.confidence = max(0.0, self.confidence - 0.10)

    def _extract_rules_from_interaction(self, user_input: str, system_response: str) -> List[str]:
        """
        Generate inverted‑mistake rules based on the interaction.

        - “NEVER do X”   where X comes from the user utterance that likely caused
          the negative reaction.
        - “ALWAYS do Y”  where Y is derived from the system response that seemed
          to mitigate the frustration (if any positive fragments are present).

        The extraction is heuristic:
        * Pull top keywords from user_input → NEVER rule.
        * Pull top keywords from system_response → ALWAYS rule (if any positive words are present).
        """
        # Keywords from the user's utterance (possible mistake source)
        user_keywords = _extract_keywords(user_input)

        # Keywords from the system's response (possible corrective action)
        response_keywords = _extract_keywords(system_response)

        never_rule = _format_rule("NEVER", user_keywords)
        always_rule = _format_rule("ALWAYS", response_keywords)

        # If the system response contains any positive cue words, keep the ALWAYS rule,
        # otherwise discard it (it likely didn't help).
        if any(word in _POSITIVE_WORDS for word in _normalize(system_response)):
            return [never_rule, always_rule]
        else:
            return [never_rule]

    # ------------------------------------------------------------------- #
    # Utility / inspection
    # ------------------------------------------------------------------- #

    def get_all_rules(self) -> List[str]:
        """Return a copy of all extracted rules."""
        return list(self.extracted_rules)


# --------------------------------------------------------------------------- #
# Simple demonstration when run as a script
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    learner = RLIFLearner()

    demo_interactions = [
        ("How do I reset my password?", "You can reset it by clicking the link."),
        ("I can't find the logout button.", "Sorry, the logout button is at the top right."),
        ("Your help page is useless.", "I apologise for the inconvenience. Let me guide you step‑by‑step."),
        ("Thanks, that worked!", "Great! Happy to help."),
    ]

    for ui, sr in demo_interactions:
        conf, new_rules = learner.process_interaction(ui, sr)
        print(f"\nUser: {ui}\nSystem: {sr}")
        print(f"Confidence: {conf:.2f}")
        if new_rules:
            print("Newly extracted rules:")
            for r in new_rules:
                print(f"  - {r}")

    print("\nAll accumulated rules:")
    for r in learner.get_all_rules():
        print(f"  * {r}")