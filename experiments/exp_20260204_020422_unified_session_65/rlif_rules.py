"""
rlif_rules.py
-------------
Rule extraction, persistence, and retrieval for RLIF.

Rules are stored in JSON Lines format inside
`learned_lessons.json` located in the same experiment directory.
Each line is a JSON object:

{
    "rule": "NEVER delete files without checking",
    "source": {
        "user_input": "...",
        "system_output": "...",
        "analysis": {...}
    },
    "timestamp": "2026-02-04T12:34:56.789Z"
}

The module provides:
- `extract_rule(sentiment, analysis, user_input, system_output)`
- `store_rule(rule_obj)`
- `load_rules()`
- `relevant_rules(context_keywords)`
"""

import json
import os
import datetime
from typing import List, Dict, Any

# Path is relative to this file's directory
_EXPERIMENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_RULES_FILE = os.path.join(_EXPERIMENT_ROOT, "learned_lessons.json")


def _ensure_rules_file():
    """Create the JSONL file if it does not exist."""
    if not os.path.exists(_RULES_FILE):
        with open(_RULES_FILE, "w", encoding="utf-8") as f:
            pass  # just create an empty file


def extract_rule(
    sentiment: str,
    analysis: Dict[str, Any],
    user_input: str,
    system_output: str,
) -> str:
    """
    Convert analysis + sentiment into a human‑readable rule.

    For negative sentiment we generate a "NEVER ..." rule.
    For positive sentiment we generate an "ALWAYS ..." rule.
    """
    missing = analysis.get("missing_keywords", [])
    if sentiment == "negative":
        if missing:
            action = f"NEVER perform actions related to {', '.join(missing)}"
        else:
            action = "NEVER repeat the problematic behavior observed"
    else:  # positive or neutral
        # Try to surface a positive habit
        overlapping = analysis.get("system_keywords", [])
        if overlapping:
            action = f"ALWAYS include {', '.join(overlapping)} when possible"
        else:
            action = "ALWAYS maintain the current successful approach"

    # Normalise spacing and punctuation
    rule = action.strip().rstrip(".")
    return rule


def store_rule(rule: str, user_input: str, system_output: str, analysis: Dict[str, Any]) -> None:
    """
    Append a rule entry to the learned_lessons.json file.
    """
    _ensure_rules_file()
    entry = {
        "rule": rule,
        "source": {
            "user_input": user_input,
            "system_output": system_output,
            "analysis": analysis,
        },
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }
    with open(_RULES_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_rules() -> List[Dict[str, Any]]:
    """Read all stored rule objects."""
    _ensure_rules_file()
    rules = []
    with open(_RULES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rules.append(json.loads(line))
                except json.JSONDecodeError:
                    # Skip malformed lines – they shouldn't happen in normal flow
                    continue
    return rules


def relevant_rules(context_keywords: List[str]) -> List[str]:
    """
    Return a list of rule strings that contain any of the supplied keywords.

    This is a very cheap substring match; more elaborate similarity can be
    added later without breaking the API.
    """
    all_rules = load_rules()
    matches = []
    lowered = [kw.lower() for kw in context_keywords]
    for entry in all_rules:
        rule_text = entry.get("rule", "")
        if any(kw in rule_text.lower() for kw in lowered):
            matches.append(rule_text)
    return matches


# Demo when run directly
if __name__ == "__main__":
    from rlif_detector import detect_sentiment
    from rlif_analyzer import analyze_issue

    ui = "I got an error and the folder was overwritten!"
    so = "delete_folder('/var/data')"
    sentiment = detect_sentiment(ui)
    analysis = analyze_issue(ui, so)
    rule = extract_rule(sentiment, analysis, ui, so)
    print("Extracted rule:", rule)
    store_rule(rule, ui, so, analysis)
    print("All stored rules:", load_rules())