import json
import os
from typing import List, Dict, Any

_LESSONS_PATH = os.path.join(
    os.path.dirname(__file__), "learned_lessons.json"
)

def _ensure_lessons_file():
    if not os.path.exists(_LESSONS_PATH):
        with open(_LESSONS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def load_rules() -> List[str]:
    """Load all stored rules from learned_lessons.json."""
    _ensure_lessons_file()
    with open(_LESSONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []

def store_rule(rule: str) -> None:
    """Append a new rule to learned_lessons.json if it is not a duplicate."""
    rule = rule.strip()
    if not rule:
        return
    _ensure_lessons_file()
    rules = load_rules()
    if rule not in rules:
        rules.append(rule)
        with open(_LESSONS_PATH, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)

def extract_rule(analysis: Dict[str, Any]) -> str:
    """
    Convert an analysis dict (output of rlif_analyzer.analyze_issue)
    into a concise rule string.
    """
    if not analysis or not analysis.get("analysis"):
        return ""

    text = analysis["analysis"].lower()

    if "overwrite" in text:
        return "Before overwriting folders, compare versions first"
    if "delete" in text:
        return "Never blindly delete without checking"
    if "powershell" in text or "bash" in text:
        return "Use PowerShell for Windows, not Unix commands in Bash tool"
    # Fallback generic rule
    return "Pay attention to user feedback and validate actions before execution"

def apply_rules_to_prompt(prompt: str) -> str:
    """
    Prepend any relevant stored rules to the incoming prompt.
    Relevance is judged by a simple keyword containment test.
    """
    rules = load_rules()
    relevant = []
    lowered = prompt.lower()
    for rule in rules:
        # Extract keywords from the rule (very naive)
        keywords = [kw.strip() for kw in rule.split(",")]
        if any(kw.lower() in lowered for kw in keywords):
            relevant.append(rule)

    if not relevant:
        return prompt

    injected = "\n".join(f"# RULE: {r}" for r in relevant)
    return f"{injected}\n{prompt}"