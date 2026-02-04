"""
rlif_learner.py
----------------
A lightweight Rule‑Learning‑From‑Interaction (RLIF) module.

Features
~~~~~~~~
* Processes a turn (user_input, system_response).
* Performs very‑light sentiment detection on the *system_response*.
* Positive sentiment → modest confidence boost for the last generated rule.
* Negative sentiment → treats the turn as a frustration event, extracts a rule
  from the interaction and stores it in an inverted “NEVER/ALWAYS” form.
* Simple in‑memory rule store with retrieval helpers.

The implementation purposefully avoids heavy dependencies (e.g. deep‑learning
models) to stay self‑contained for the experiment environment.
"""

import re
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# ---------------------------------------------------------------------------
# Very small sentiment heuristic
# ---------------------------------------------------------------------------
_POSITIVE_WORDS = {
    "good", "great", "awesome", "nice", "thanks", "thank you", "perfect",
    "well", "correct", "helpful", "liked", "love", "excellent"
}
_NEGATIVE_WORDS = {
    "bad", "terrible", "wrong", "incorrect", "hate", "useless", "frustrating",
    "annoy", "annoying", "confusing", "not helpful", "problem", "error"
}


def simple_sentiment(text: str) -> str:
    """
    Very naive sentiment detector.

    Returns
    -------
    'positive', 'negative' or 'neutral'
    """
    lowered = text.lower()
    pos_hits = sum(word in lowered for word in _POSITIVE_WORDS)
    neg_hits = sum(word in lowered for word in _NEGATIVE_WORDS)

    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Rule extraction utilities
# ---------------------------------------------------------------------------
def _extract_key_action(sentence: str) -> Optional[str]:
    """
    Extract a verb‑noun phrase that looks like an action from a sentence.
    Very naive: grabs the first verb (identified by simple regex) plus the
    following noun (if any).

    Example
    -------
    "Do not send private data" -> "send private data"
    """
    # Remove punctuation for easier regex handling
    cleaned = re.sub(r"[^\w\s]", "", sentence.lower())
    # Simple pattern: optional "do not"/"never", then verb, then rest
    match = re.search(r"(?:do not|never|always)?\s*([a-z]+)\s+(.*)", cleaned)
    if match:
        verb = match.group(1)
        rest = match.group(2).strip()
        return f"{verb} {rest}".strip()
    return None


def _invert_action(action: str, sentiment: str) -> str:
    """
    Turn an extracted action into a rule string.
    Positive sentiment → "ALWAYS do ..."
    Negative sentiment → "NEVER do ..."
    """
    prefix = "ALWAYS" if sentiment == "positive" else "NEVER"
    # Capitalise first word of action for readability
    action_cap = action[0].upper() + action[1:]
    return f"{prefix} {action_cap}"


# ---------------------------------------------------------------------------
# Core learner class
# ---------------------------------------------------------------------------
class RLIFLearner:
    """
    Rule Learning From Interaction (RLIF) engine.

    The learner is intended to be called after each turn of a dialogue.
    It analyses the system's response for sentiment and, when a negative
    sentiment is detected, extracts a rule from the user input / system
    response pair.
    """

    def __init__(self):
        # Rules are stored as a list of dicts for easy JSON export
        self.rules: List[Dict] = []
        # Simple confidence score per rule (0.0‑1.0)
        self._rule_confidence: Dict[int, float] = defaultdict(lambda: 0.5)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def process_turn(self, user_input: str, system_response: str) -> None:
        """
        Process a single interaction turn.

        Parameters
        ----------
        user_input : str
            What the user said / typed.
        system_response : str
            The system's reply to that input.
        """
        sentiment = simple_sentiment(system_response)
        if sentiment == "positive":
            self._apply_positive_boost()
        elif sentiment == "negative":
            self._handle_frustration(user_input, system_response)

    def get_rules(self, as_json: bool = False) -> List[Dict] | str:
        """
        Retrieve the learned rules.

        Parameters
        ----------
        as_json : bool, optional
            If True, returns a JSON string; otherwise returns a list of dicts.

        Returns
        -------
        list or str
        """
        if as_json:
            return json.dumps(self.rules, indent=2, default=str)
        return self.rules

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _apply_positive_boost(self) -> None:
        """
        When a positive sentiment is observed we slightly increase the confidence
        of the most recent rule (if any). This models the "mild boost" described.
        """
        if not self.rules:
            return
        last_idx = len(self.rules) - 1
        old_conf = self._rule_confidence[last_idx]
        new_conf = min(1.0, old_conf + 0.1)  # boost by 0.1, cap at 1.0
        self._rule_confidence[last_idx] = new_conf
        self.rules[last_idx]["confidence"] = new_conf

    def _handle_frustration(self, user_input: str, system_response: str) -> None:
        """
        Negative sentiment → treat as frustration, attempt to extract a rule.
        """
        # Try to extract an actionable phrase from the user input first,
        # falling back to the system response.
        candidate = _extract_key_action(user_input) or _extract_key_action(system_response)
        if not candidate:
            # Fallback: use a generic placeholder rule
            candidate = "handle unknown situation"

        # Invert the extracted action into a rule string
        rule_text = _invert_action(candidate, sentiment="negative")

        # Store rule with metadata
        rule_entry = {
            "id": len(self.rules),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "rule": rule_text,
            "source_user_input": user_input,
            "source_system_response": system_response,
            "confidence": self._rule_confidence[len(self.rules)]
        }
        self.rules.append(rule_entry)

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------
    @staticmethod
    def load_from_json(json_str: str) -> "RLIFLearner":
        """
        Re‑create a learner from a JSON string produced by ``get_rules(as_json=True)``.
        """
        learner = RLIFLearner()
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                learner.rules = data
                for idx, rule in enumerate(data):
                    learner._rule_confidence[idx] = rule.get("confidence", 0.5)
        except json.JSONDecodeError:
            pass
        return learner


# ---------------------------------------------------------------------------
# Simple demo when run as a script (not required for the experiment but handy)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    learner = RLIFLearner()
    demo = [
        ("Can you send me the report?", "Sure, here it is."),
        ("Why didn't you include the summary?", "Sorry, I missed it."),
        ("That was terrible, you forgot the summary!", "Apologies, I will include it next time."),
        ("Thanks, that works!", "Glad it helped!"),
    ]

    for user, resp in demo:
        learner.process_turn(user, resp)

    print("Learned rules:")
    print(learner.get_rules(as_json=True))