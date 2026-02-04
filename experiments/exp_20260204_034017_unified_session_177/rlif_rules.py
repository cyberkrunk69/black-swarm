import json
import os
import threading
from typing import List, Dict

_RULES_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "learned_lessons.json")
)

_lock = threading.Lock()


def _ensure_file():
    """Create an empty JSON array file if it does not exist."""
    if not os.path.exists(_RULES_FILE):
        with open(_RULES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_rules() -> List[Dict]:
    """Return the list of stored rules."""
    _ensure_file()
    with _lock, open(_RULES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_rules(rules: List[Dict]):
    """Write the full rule list back to disk (thread‑safe)."""
    with _lock, open(_RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def _deduplicate(rules: List[Dict], new_rule: Dict) -> List[Dict]:
    """Add *new_rule* if an equivalent rule does not already exist."""
    for r in rules:
        if r.get("text") == new_rule.get("text"):
            # Existing rule – optionally update metadata (e.g., count)
            r["hits"] = r.get("hits", 1) + 1
            return rules
    # New rule – initialise metadata
    new_rule.setdefault("hits", 1)
    rules.append(new_rule)
    return rules


def extract_rule_from_analysis(analysis: str) -> str:
    """
    Convert a short analysis string into a concrete “always/never” rule.
    Very simple heuristic – prepend “Never …” if the analysis contains a negative
    verb, otherwise “Always …”.
    """
    analysis = analysis.strip().rstrip(".")
    # Keywords that imply a prohibition.
    forbid_keywords = ["overwrite", "delete", "remove", "ignore", "skip"]
    for kw in forbid_keywords:
        if kw in analysis.lower():
            # Create a “Never …” rule.
            return f"Never {analysis.lower()}."
    # Default to a positive recommendation.
    return f"Always {analysis.lower()}."
    

def store_rule(analysis: str):
    """
    High‑level helper used by the RLIF pipeline:
    1. Convert analysis → rule text.
    2. Load current rule set.
    3. Deduplicate / update hit count.
    4. Persist.
    """
    rule_text = extract_rule_from_analysis(analysis)
    rule_entry = {
        "text": rule_text,
        "source_analysis": analysis,
    }

    rules = load_rules()
    rules = _deduplicate(rules, rule_entry)
    _save_rules(rules)


def get_applicable_rules(context: str) -> List[str]:
    """
    Very naive matcher – returns all stored rules whose text contains a keyword
    present in the current *context* (e.g., the upcoming user prompt).
    """
    rules = load_rules()
    lowered = context.lower()
    applicable = [r["text"] for r in rules if any(tok in lowered for tok in r["text"].lower().split())]
    return applicable