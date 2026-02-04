"""
rlif_learner.py
----------------
A lightweight Rule‑Learning Interaction Framework (RLIF) learner.

Purpose
-------
* Listen to user‑assistant exchanges.
* Perform a quick sentiment analysis on the assistant’s response.
* When sentiment is **positive** – apply a mild boost to the internal confidence
  scores of the currently active rule set.
* When sentiment is **negative** – run a “frustration analysis”, extract the
  offending fragment(s) and automatically synthesize corrective rules.
* Mistakes are inverted into explicit “NEVER …” / “ALWAYS …” rules to guide future
  behavior.

Design
------
* `RLIFLearner` – the main class.
* Uses the `vaderSentiment` package (built‑in to many Python envs) for sentiment
  scoring – no heavyweight ML models required.
* Rules are stored in an in‑memory dictionary and can be persisted via JSON.
* The public API is intentionally tiny:
    - `process_interaction(user_input: str, assistant_response: str) -> None`
    - `export_rules(path: str) -> None`
    - `load_rules(path: str) -> None`

The module is deliberately self‑contained and does not touch any of the
read‑only core system files.
"""

import json
import re
from collections import defaultdict
from typing import Dict, List, Tuple

# Sentiment analysis – VADER (part of nltk).  Fallback to a simple heuristic if not present.
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _sent_analyzer = SentimentIntensityAnalyzer()
except Exception:  # pragma: no cover
    _sent_analyzer = None


class RLIFLearner:
    """
    Rule‑Learning Interaction Framework learner.

    Attributes
    ----------
    rules : Dict[str, Dict]
        Mapping from a rule identifier to its metadata:
        {
            "text": str,               # human‑readable rule
            "confidence": float,       # 0.0 – 1.0
            "hits": int,               # how many times rule applied
        }
    """

    POSITIVE_THRESHOLD = 0.3   # VADER compound > 0.3 → positive
    NEGATIVE_THRESHOLD = -0.3  # VADER compound < -0.3 → negative

    def __init__(self) -> None:
        self.rules: Dict[str, Dict] = {}
        self._next_rule_id = 1

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def process_interaction(self, user_input: str, assistant_response: str) -> None:
        """
        Analyse a single interaction and update the rule base.

        Parameters
        ----------
        user_input : str
            What the user said.
        assistant_response : str
            The assistant's reply that will be evaluated.
        """
        sentiment = self._detect_sentiment(assistant_response)

        if sentiment > self.POSITIVE_THRESHOLD:
            self._apply_positive_boost()
        elif sentiment < self.NEGATIVE_THRESHOLD:
            self._handle_negative_feedback(user_input, assistant_response)
        # Neutral sentiment → no rule change

    def export_rules(self, path: str) -> None:
        """Serialise the rule dictionary to a JSON file."""
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(self.rules, fp, indent=2, ensure_ascii=False)

    def load_rules(self, path: str) -> None:
        """Load a previously exported rule set."""
        with open(path, "r", encoding="utf-8") as fp:
            self.rules = json.load(fp)
        # Re‑compute next rule id
        ids = [int(k.split("_")[-1]) for k in self.rules.keys() if "_" in k]
        self._next_rule_id = max(ids, default=0) + 1

    # --------------------------------------------------------------------- #
    # Internals – Sentiment
    # --------------------------------------------------------------------- #
    def _detect_sentiment(self, text: str) -> float:
        """
        Return a compound sentiment score in the range [-1, 1].

        If VADER is unavailable, a very naive heuristic based on
        positive/negative word lists is used.
        """
        if _sent_analyzer:
            return _sent_analyzer.polarity_scores(text)["compound"]

        # ---- Simple fallback -------------------------------------------------
        pos_words = {"good", "great", "nice", "thanks", "thank", "awesome", "perfect"}
        neg_words = {"bad", "wrong", "error", "mistake", "incorrect", "fail", "sorry"}
        tokens = re.findall(r"\b\w+\b", text.lower())
        score = (len([t for t in tokens if t in pos_words]) -
                 len([t for t in tokens if t in neg_words]))
        # Normalise to [-1, 1]
        return max(min(score / max(len(tokens), 1), 1.0), -1.0)

    # --------------------------------------------------------------------- #
    # Internals – Positive handling
    # --------------------------------------------------------------------- #
    def _apply_positive_boost(self) -> None:
        """
        Mildly increase confidence of all existing rules.
        """
        for meta in self.rules.values():
            meta["confidence"] = min(1.0, meta["confidence"] + 0.05)

    # --------------------------------------------------------------------- #
    # Internals – Negative handling
    # --------------------------------------------------------------------- #
    def _handle_negative_feedback(self, user_input: str, assistant_response: str) -> None:
        """
        Extract the problematic fragment(s) and synthesize corrective rules.
        """
        # 1. Identify likely offending phrase(s) – a naive approach:
        #    Look for the longest common subsequence that appears in both strings.
        #    In practice this gives us a hint about what the assistant repeated
        #    incorrectly.
        offending = self._extract_offending_phrase(user_input, assistant_response)

        # 2. Build two complementary rules:
        #    * NEVER do the offending behaviour.
        #    * ALWAYS do the opposite (if we can infer it).
        if offending:
            never_rule = f"NEVER {offending.strip().lower()}"
            always_rule = self._invert_phrase(offending)

            self._add_rule(never_rule, confidence=0.9)
            if always_rule:
                self._add_rule(always_rule, confidence=0.7)

    def _extract_offending_phrase(self, user: str, bot: str) -> str:
        """
        Very simple heuristic: return the longest substring of the bot response
        that also appears in the user input. If none found, fall back to the
        whole bot response (treated as a generic mistake).
        """
        user_tokens = user.lower().split()
        bot_tokens = bot.lower().split()

        # Build all substrings of bot tokens and keep the longest that appears in user.
        longest_match = ""
        for i in range(len(bot_tokens)):
            for j in range(i + 1, len(bot_tokens) + 1):
                candidate = " ".join(bot_tokens[i:j])
                if candidate in " ".join(user_tokens) and len(candidate) > len(longest_match):
                    longest_match = candidate
        return longest_match or " ".join(bot_tokens)

    def _invert_phrase(self, phrase: str) -> str:
        """
        Produce a simplistic opposite of a phrase.
        Example: "never delete files" → "always keep files"
        This is not exhaustive – it only handles a few common patterns.
        """
        phrase = phrase.strip().lower()
        # Basic pattern replacements
        replacements = [
            (r"\bnever\b", "always"),
            (r"\bnot\b", ""),
            (r"\bdo not\b", "do"),
            (r"\bdon't\b", "do"),
            (r"\bavoid\b", "prefer"),
            (r"\bincorrect\b", "correct"),
            (r"\bmistake\b", "correct action"),
        ]

        for pattern, repl in replacements:
            if re.search(pattern, phrase):
                phrase = re.sub(pattern, repl, phrase)
                # After a successful replacement we stop – the phrase is now inverted.
                break
        else:
            # If no pattern matched, prepend "always" as a generic positive form.
            phrase = f"always {phrase}"

        # Clean up double spaces
        phrase = re.sub(r"\s{2,}", " ", phrase).strip()
        # Capitalise first word for readability
        return phrase.capitalize()

    def _add_rule(self, text: str, confidence: float = 0.5) -> None:
        """
        Insert a new rule into the store or update an existing one.
        """
        rule_id = f"rule_{self._next_rule_id}"
        self.rules[rule_id] = {
            "text": text,
            "confidence": confidence,
            "hits": 0,
        }
        self._next_rule_id += 1

    # --------------------------------------------------------------------- #
    # Optional utility – rule lookup (not required but handy)
    # --------------------------------------------------------------------- #
    def get_rules(self) -> List[Tuple[str, Dict]]:
        """Return a list of (rule_id, metadata) tuples sorted by confidence."""
        return sorted(self.rules.items(), key=lambda kv: kv[1]["confidence"], reverse=True)


# ------------------------------------------------------------------------- #
# Simple demo when run as a script (does not interfere with library usage)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    learner = RLIFLearner()
    # Simulated interactions
    interactions = [
        ("How do I delete a file?", "You should never delete files."),
        ("I need to remove temp.txt", "Sure, I will delete temp.txt now."),
        ("Thanks, that worked!", "Glad it helped!"),
    ]

    for usr, bot in interactions:
        learner.process_interaction(usr, bot)

    print("\nExtracted Rules:")
    for rid, meta in learner.get_rules():
        print(f"{rid}: {meta['text']} (confidence={meta['confidence']:.2f})")