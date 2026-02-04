"""
rlif_learner.py

A lightweight Rule‑Learning Interaction Framework (RLIF) learner that:
* Detects sentiment in the system's response to a user interaction.
* Gives a mild boost on positive sentiment.
* Performs frustration analysis on negative sentiment and extracts
  corrective rules by inverting the problematic behaviour.

The implementation is intentionally simple – it relies on a small
keyword‑based sentiment detector to avoid heavyweight dependencies.
The learner can be extended later with more sophisticated NLP models.

Usage
-----
    from rlif_learner import RLIFLearner

    learner = RLIFLearner()
    rule = learner.process_interaction(user_msg, system_reply)
    if rule:
        print("New rule extracted:", rule)
"""

import re
from collections import Counter
from typing import List, Optional


class SentimentDetector:
    """
    Very small rule‑based sentiment detector.
    Positive keywords increase score, negative keywords decrease it.
    The final polarity is:
        > 0  -> Positive
        == 0 -> Neutral
        < 0  -> Negative
    """

    POSITIVE_WORDS = {
        "good", "great", "excellent", "awesome", "nice", "thanks",
        "thank you", "perfect", "well", "amazing", "fantastic",
        "👍", "😊", "😀", "love", "liked", "like", "enjoy"
    }

    NEGATIVE_WORDS = {
        "bad", "terrible", "awful", "hate", "horrible", "wrong",
        "incorrect", "mistake", "error", "frustrated", "annoyed",
        "sad", "😞", "👎", "dislike", "doesn't work", "not working",
        "fail", "failed", "problem", "issue"
    }

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        # Lower‑case, strip punctuation, split on whitespace
        cleaned = re.sub(r"[^\w\s']", " ", text.lower())
        return cleaned.split()

    @classmethod
    def polarity(cls, text: str) -> int:
        tokens = cls._tokenize(text)
        pos = sum(tok in cls.POSITIVE_WORDS for tok in tokens)
        neg = sum(tok in cls.NEGATIVE_WORDS for tok in tokens)
        return pos - neg

    @classmethod
    def is_positive(cls, text: str) -> bool:
        return cls.polarity(text) > 0

    @classmethod
    def is_negative(cls, text: str) -> bool:
        return cls.polarity(text) < 0


class RuleExtractor:
    """
    Extracts a corrective rule from a user utterance that caused frustration.
    The extraction strategy is deliberately straightforward:
        * Identify a verb phrase (the first word that looks like a verb) – if none,
          fall back to the whole utterance.
        * Produce an inverted rule:
              - Negative interaction → "NEVER do <phrase>"
              - Positive interaction → "ALWAYS do <phrase>"
    """

    # Very naive verb list – can be expanded.
    VERBS = {
        "run", "execute", "open", "close", "save", "delete", "create",
        "write", "read", "send", "receive", "click", "press", "select",
        "choose", "add", "remove", "update", "install", "uninstall",
        "start", "stop", "restart", "login", "logout", "sign", "enter",
        "type", "search", "find", "load", "fetch", "process"
    }

    @classmethod
    def _first_verb_phrase(cls, text: str) -> str:
        tokens = text.strip().split()
        for i, token in enumerate(tokens):
            # Simple heuristic: token is a verb (case‑insensitive) and not a stop word
            if token.lower() in cls.VERBS:
                # Return from the verb onward as the phrase
                return " ".join(tokens[i:])
        # Fallback – return the whole cleaned utterance
        return text.strip()

    @classmethod
    def build_rule(cls, user_input: str, sentiment: str) -> str:
        """
        sentiment: "positive" or "negative"
        """
        phrase = cls._first_verb_phrase(user_input)
        if sentiment == "negative":
            return f"NEVER do {phrase}"
        else:  # positive
            return f"ALWAYS do {phrase}"


class RLIFLearner:
    """
    Core learner that processes a user interaction, detects sentiment,
    optionally boosts internal confidence, and extracts rules on negative
    feedback.
    """

    def __init__(self):
        # Simple counters to illustrate a "boost" on positive feedback.
        self.positive_interactions = 0
        self.negative_interactions = 0
        self.extracted_rules: List[str] = []

    def process_interaction(self, user_input: str, system_response: str) -> Optional[str]:
        """
        Analyze a single interaction.

        Parameters
        ----------
        user_input : str
            The raw text the user typed.
        system_response : str
            The assistant's reply to that input.

        Returns
        -------
        Optional[str]
            A newly extracted rule if sentiment was negative (or positive, if you
            want a reinforcement rule). Returns ``None`` when no rule is generated.
        """
        # Sentiment analysis on the system's *response* (as per spec)
        if SentimentDetector.is_positive(system_response):
            self.positive_interactions += 1
            # Mild boost – could be used by downstream components.
            # Here we simply log the boost.
            # (No rule is generated for positive sentiment unless you want reinforcement.)
            return None

        if SentimentDetector.is_negative(system_response):
            self.negative_interactions += 1
            rule = RuleExtractor.build_rule(user_input, sentiment="negative")
            self.extracted_rules.append(rule)
            return rule

        # Neutral – nothing to do.
        return None

    # --------------------------------------------------------------------- #
    # Helper utilities – optional but handy for experimentation
    # --------------------------------------------------------------------- #
    def summary(self) -> dict:
        """Return a quick summary of the learner's internal state."""
        return {
            "positive_interactions": self.positive_interactions,
            "negative_interactions": self.negative_interactions,
            "total_rules": len(self.extracted_rules),
            "rules": self.extracted_rules.copy(),
        }

    def reset(self) -> None:
        """Clear all counters and extracted rules."""
        self.positive_interactions = 0
        self.negative_interactions = 0
        self.extracted_rules.clear()


# ------------------------------------------------------------------------- #
# Simple manual test (executed only when run as a script)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    learner = RLIFLearner()

    # Simulated interactions
    interactions = [
        ("I tried to open the file", "I'm sorry, that didn't work."),
        ("Please save my changes", "All right, saved!"),
        ("Can you delete the temp folder?", "Oops, something went wrong."),
    ]

    for ui, resp in interactions:
        rule = learner.process_interaction(ui, resp)
        if rule:
            print(f"Extracted rule: {rule}")

    print("\nLearner summary:")
    print(learner.summary())