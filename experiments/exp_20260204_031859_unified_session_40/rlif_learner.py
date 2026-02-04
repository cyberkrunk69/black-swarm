"""
rlif_learner.py
----------------
A lightweight Rule‑Learning Interaction Framework (RLIF) learner that
- receives user interaction logs,
- performs sentiment analysis on the user’s textual responses,
- adjusts a simple confidence score for the system based on sentiment,
- extracts actionable rules from the interaction, especially when negative
  sentiment is detected,
- stores rules in an in‑memory list (or optional persistence).

The implementation deliberately avoids any heavy dependencies; it uses the
built‑in `re` module for simple keyword‑based sentiment heuristics and a
tiny rule‑extraction engine.  This keeps the file self‑contained and suitable
for rapid experimentation in the `exp_20260204_031859_unified_session_40`
workspace.
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Any


class SentimentDetector:
    """
    Very simple rule‑based sentiment detector.
    Positive sentiment keywords increase the confidence boost.
    Negative sentiment keywords trigger frustration analysis.
    """

    POSITIVE_PATTERNS = [
        r"\bthanks?\b",
        r"\bgreat\b",
        r"\bgood\b",
        r"\bawesome\b",
        r"\blove\b",
        r"\bperfect\b",
        r"\bnice\b",
        r"\bwell done\b",
    ]

    NEGATIVE_PATTERNS = [
        r"\bnot (helpful|useful|good|working)\b",
        r"\bdoesn't work\b",
        r"\bdoes not work\b",
        r"\bconfusing\b",
        r"\bbad\b",
        r"\bwrong\b",
        r"\berror\b",
        r"\bproblem\b",
        r"\bfrustrat(ed|ing)\b",
        r"\bcan't\b",
        r"\bcannot\b",
        r"\bfailed\b",
    ]

    def __init__(self):
        self.pos_regex = re.compile("|".join(self.POSITIVE_PATTERNS), re.I)
        self.neg_regex = re.compile("|".join(self.NEGATIVE_PATTERNS), re.I)

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Returns a dict:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "score": float (positive >0, negative <0, 0 neutral),
            "matches": List[str] (matched keywords)
        }
        """
        matches = []
        sentiment = "neutral"
        score = 0.0

        pos_matches = self.pos_regex.findall(text)
        if pos_matches:
            sentiment = "positive"
            score += 0.1 * len(pos_matches)  # mild boost per positive cue
            matches.extend([m.lower() for m in pos_matches])

        neg_matches = self.neg_regex.findall(text)
        if neg_matches:
            # Negative overrides positive if both appear
            sentiment = "negative"
            score -= 0.2 * len(neg_matches)  # stronger penalty per negative cue
            matches.extend([m.lower() for m in neg_matches])

        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "matches": matches,
        }


class RuleExtractor:
    """
    Generates simple imperative rules from interaction context.
    - Positive interactions: optional reinforcement (e.g., "ALWAYS do X").
    - Negative interactions: generate corrective rules (e.g., "NEVER do X").
    """

    def __init__(self):
        # Store rules as strings; could be persisted later
        self.rules: List[str] = []

    def _clean_action(self, text: str) -> str:
        """
        Very naive extraction of the action phrase.
        Looks for verbs followed by optional objects.
        """
        # Find first verb (simple heuristic)
        verb_match = re.search(r"\b(\w+ing|\bdo\b|\buse\b|\brun\b|\bcall\b|\bexecute\b)\b", text, re.I)
        if verb_match:
            start = verb_match.start()
            # Grab up to next punctuation or end of sentence
            snippet = text[start:].split('.')[0].split('!')[0].split('?')[0]
            return snippet.strip()
        return ""

    def add_rule_from_interaction(self, user_text: str, sentiment: str):
        """
        Derives a rule based on sentiment.
        - Positive: "ALWAYS <action>"
        - Negative: "NEVER <action>"
        - Neutral: no rule
        """
        action = self._clean_action(user_text)
        if not action:
            return  # nothing actionable

        rule = None
        if sentiment == "positive":
            rule = f"ALWAYS {action.upper()}"
        elif sentiment == "negative":
            rule = f"NEVER {action.upper()}"

        if rule and rule not in self.rules:
            self.rules.append(rule)

    def get_rules(self) -> List[str]:
        return self.rules.copy()

    def to_json(self) -> str:
        """Serialize rules to JSON for persistence."""
        return json.dumps({"rules": self.rules}, indent=2)


class RLIFLearner:
    """
    Orchestrates sentiment detection and rule extraction.
    Usage:
        learner = RLIFLearner()
        learner.process_interaction(user_id, user_text)
        print(learner.get_rules())
    """

    def __init__(self):
        self.sentiment_detector = SentimentDetector()
        self.rule_extractor = RuleExtractor()
        # Simple confidence map per user (could be expanded)
        self.user_confidence: Dict[str, float] = {}

    def _update_confidence(self, user_id: str, sentiment_info: Dict[str, Any]):
        """
        Adjust confidence based on sentiment score.
        Positive => mild boost.
        Negative => penalty.
        """
        delta = sentiment_info["score"]
        self.user_confidence[user_id] = self.user_confidence.get(user_id, 0.0) + delta
        # Clamp between -1.0 and +1.0
        self.user_confidence[user_id] = max(min(self.user_confidence[user_id], 1.0), -1.0)

    def process_interaction(self, user_id: str, user_text: str) -> Dict[str, Any]:
        """
        Main entry point.
        Returns a dict with sentiment analysis, updated confidence and any new rule.
        """
        sentiment_info = self.sentiment_detector.analyze(user_text)
        self._update_confidence(user_id, sentiment_info)

        # Extract rule if sentiment is not neutral
        if sentiment_info["sentiment"] != "neutral":
            self.rule_extractor.add_rule_from_interaction(user_text, sentiment_info["sentiment"])

        result = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "text": user_text,
            "sentiment": sentiment_info["sentiment"],
            "sentiment_score": sentiment_info["score"],
            "confidence": round(self.user_confidence[user_id], 3),
            "new_rules": self.rule_extractor.get_rules(),
        }
        return result

    def get_rules(self) -> List[str]:
        return self.rule_extractor.get_rules()

    def export_rules(self, filepath: str = None) -> str:
        """
        Returns JSON representation of rules.
        If `filepath` is provided, writes the JSON to that file.
        """
        json_str = self.rule_extractor.to_json()
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str


# ----------------------------------------------------------------------
# Example usage (can be removed or guarded by __name__ guard in production)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    learner = RLIFLearner()
    interactions = [
        ("user1", "Thanks, that helped a lot!"),
        ("user2", "It doesn't work when I try to run the script."),
        ("user1", "Great, now it's perfect."),
        ("user3", "I'm frustrated because the command fails."),
    ]

    for uid, txt in interactions:
        out = learner.process_interaction(uid, txt)
        print(json.dumps(out, indent=2))

    print("\n=== Extracted Rules ===")
    print("\n".join(learner.get_rules()))