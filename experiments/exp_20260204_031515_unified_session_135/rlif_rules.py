import json
import os
from typing import List

RULES_FILE = os.path.join(
    os.path.dirname(__file__), "learned_lessons.json"
)

def _ensure_rules_file():
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)

def load_rules() -> List[str]:
    """Load all stored rules."""
    _ensure_rules_file()
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def store_rule(rule: str):
    """Append a new rule to the persistent storage."""
    _ensure_rules_file()
    rules = load_rules()
    if rule not in rules:
        rules.append(rule)
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(rules, f, indent=2)

def extract_rule(analysis: str, user_input: str) -> str:
    """
    Convert a root‑cause analysis into a concrete actionable rule.
    Very simple heuristic: look for verbs and objects in the analysis.
    """
    analysis_lower = analysis.lower()
    # Example patterns – expand as needed.
    if "delete" in analysis_lower and "check" not in analysis_lower:
        return "Never delete files without checking existence first."
    if "overwrite" in analysis_lower and "compare" not in analysis_lower:
        return "Always compare versions before overwriting folders."
    if "powershell" in analysis_lower and "bash" in analysis_lower:
        return "Use PowerShell for Windows tasks, not Bash commands."
    # Fallback generic rule.
    return f"ALWAYS consider: {analysis.strip()}"

def apply_rules_to_prompt(prompt: str) -> str:
    """
    Inject relevant learned rules into a new prompt.
    Very naive implementation – prepend all rules.
    """
    rules = load_rules()
    if not rules:
        return prompt
    rules_blob = "\n".join(f"# RULE: {r}" for r in rules)
    return f"{rules_blob}\n\n{prompt}"