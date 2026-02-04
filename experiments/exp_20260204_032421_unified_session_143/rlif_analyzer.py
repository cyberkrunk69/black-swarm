import json
from typing import Dict, Any
from .rlif_detector import Sentiment, detect_sentiment

# Placeholder for a "larger model" call – in a real system this would invoke
# an LLM with a richer prompt.  Here we keep it deterministic and cheap.
def _mock_large_model_analysis(user_input: str, system_output: str) -> str:
    # Very naive root‑cause extraction based on keyword presence.
    if "overwrite" in user_input.lower() or "overwrite" in system_output.lower():
        return "User was upset because a folder was overwritten without version check."
    if "delete" in user_input.lower() or "delete" in system_output.lower():
        return "User expressed frustration about an unexpected deletion."
    if "powershell" in user_input.lower() or "bash" in system_output.lower():
        return "User is confused about mixed Windows/Unix command usage."
    return "General dissatisfaction detected."

def analyze_issue(user_input: str, system_output: str) -> Dict[str, Any]:
    """
    Analyze a negative interaction and return a structured description.
    The function is only invoked when Sentiment.NEGATIVE is detected.
    """
    sentiment = detect_sentiment(user_input)
    if sentiment != Sentiment.NEGATIVE:
        return {"sentiment": sentiment.value, "analysis": None}

    # In a production environment replace this with an actual LLM call.
    root_cause = _mock_large_model_analysis(user_input, system_output)

    return {
        "sentiment": sentiment.value,
        "analysis": root_cause,
        "user_input": user_input,
        "system_output": system_output,
    }