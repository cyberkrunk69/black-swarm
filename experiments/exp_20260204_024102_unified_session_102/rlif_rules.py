"""
rlif_rules.py

Rule extraction, storage, and retrieval for Reinforcement Learning from Immediate
Feedback (RLIF). When a failure is detected, this module creates an "inverse"
rule (e.g., "Never do X") and persists it to `learned_lessons.json`. Future
sessions can query the stored rules and inject the most relevant ones into
prompts.

The rule format stored in JSON:
{
    "id": "<uuid>",
    "timestamp": "<ISO‑8601>",
    "source_message": "<original user message>",
    "cause": "<short root‑cause extracted by rlif_analyzer>",
    "rule": "<generated rule string>",
    "tags": ["frustration", "auto"]
}
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict

# Directory for RLIF artefacts – same folder as this file.
_BASE_DIR = os.path.abspath(os.path.dirname(__file__))
_RULES_FILE = os.path.join(_BASE_DIR, "learned_lessons.json")


def _load_rules() -> List[Dict]:
    if not os.path.exists(_RULES_FILE):
        return []
    try:
        with open(_RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # pragma: no cover – defensive
        return []


def _save_rules(rules: List[Dict]) -> None:
    with open(_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def _generate_inverse_rule(cause: str) -> str:
    """
    Very simple rule generator. In a production system you would likely use a
    language model to phrase the rule nicely. Here we apply a few heuristics:

    - If the cause starts with a verb, prepend "Never ".
    - If the cause looks like a recommendation, prepend "Always ".
    - Fallback: "Never do {cause}".
    """
    cause = cause.strip().rstrip(".")
    if not cause:
        return "Never do unknown operation"

    # Heuristic: if cause begins with "use" or "run" -> suggest ALWAYS
    first_word = cause.split()[0].lower()
    if first_word in {"use", "run", "prefer", "choose"}:
        return f"Always {cause}"
    else:
        return f"Never {cause}"


def add_rule_from_feedback(user_message: str, cause: str) -> Dict:
    """
    Create a rule from a failure cause and persist it.

    Parameters
    ----------
    user_message : str
        Original user feedback that triggered the analysis.
    cause : str
        Short description of the root cause (output of rlif_analyzer).

    Returns
    -------
    dict
        The rule entry that was added.
    """
    rule_text = _generate_inverse_rule(cause)

    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_message": user_message,
        "cause": cause,
        "rule": rule_text,
        "tags": ["frustration", "auto"],
    }

    rules = _load_rules()
    rules.append(entry)
    _save_rules(rules)

    return entry


def get_relevant_rules(context_keywords: List[str], limit: int = 5) -> List[str]:
    """
    Retrieve up to `limit` rules whose text contains any of the supplied keywords.
    Simple substring matching is used; more advanced semantic search can replace
    this later.

    Parameters
    ----------
    context_keywords : list[str]
        Keywords extracted from the current task (e.g., ["windows", "powershell"]).
    limit : int
        Maximum number of rules to return.

    Returns
    -------
    list[str]
        List of rule strings.
    """
    if not context_keywords:
        return []

    all_rules = _load_rules()
    matches = []

    for entry in all_rules:
        rule = entry.get("rule", "").lower()
        if any(kw.lower() in rule for kw in context_keywords):
            matches.append(entry["rule"])

    # Preserve insertion order (oldest first) and cut to limit
    return matches[:limit]


# Simple demo when run directly
if __name__ == "__main__":
    # Simulate a negative feedback flow
    demo_user_msg = "It failed to copy the folder because I overwrote existing files."
    from rlif_analyzer import analyze_failure

    cause = analyze_failure(demo_user_msg, {})
    print("Cause:", cause)

    rule_entry = add_rule_from_feedback(demo_user_msg, cause)
    print("New rule stored:", rule_entry["rule"])

    # Retrieve rules relevant to "folder"
    print("Relevant rules:", get_relevant_rules(["folder"]))