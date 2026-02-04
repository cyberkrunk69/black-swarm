import json
import os
from typing import Dict, Any

# Path to the persistent rule store – shared with rlif_rules.
_RULES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "learned_lessons.json")
)


def _load_context() -> Dict[str, Any]:
    """
    Load any auxiliary context that may help the analyzer.
    For now we keep it simple – read the existing rule file so the analyzer can
    avoid duplicate advice.
    """
    if os.path.exists(_RULES_PATH):
        try:
            with open(_RULES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def analyze_failure(user_prompt: str, assistant_response: str, user_feedback: str) -> str:
    """
    Perform a lightweight root‑cause analysis for a negative interaction.
    This stub mimics a “larger model” call by applying heuristic rules.
    In a production system you would replace this with a call to an LLM
    (e.g., OpenAI gpt‑4) that receives the full conversation history.

    Returns a short description of what went wrong, suitable for rule extraction.
    """
    # Simple heuristic: look for keywords that indicate the nature of the failure.
    lowered = user_feedback.lower()

    if "version" in lowered or "overwrite" in lowered:
        return "Potential overwriting of files without version check."
    if "powershell" in lowered or "bash" in lowered:
        return "Mismatched shell tool for the target OS."
    if "delete" in lowered and "check" not in lowered:
        return "Deletion performed without prior existence check."
    if "timeout" in lowered or "slow" in lowered:
        return "Operation took too long – may need retries or async handling."

    # Fallback generic analysis.
    return "General error – unclear root cause from feedback."