"""
rlif_analyzer.py

Root‑cause analysis component for RLIF. When a negative sentiment is detected,
this module is invoked to produce a concise description of what likely went
wrong. The implementation uses a lightweight heuristic approach, but it also
provides a hook (`run_deep_analysis`) where a larger LLM can be called if the
environment permits.

The public API:
    analyze_failure(user_message: str, system_context: dict) -> str
"""

import json
import os
from typing import Dict

# Path to a (optional) deeper‑analysis model configuration.
_DEEP_MODEL_CONFIG = os.getenv("RLIF_DEEP_MODEL_CONFIG", "")


def _simple_heuristic(message: str) -> str:
    """
    Very fast heuristic that extracts a possible cause from the user message.
    It looks for common patterns like "cannot X", "error Y", "failed to Z".
    """
    patterns = [
        r"cannot\s+([^\.\!\?]+)",
        r"can't\s+([^\.\!\?]+)",
        r"failed\s+to\s+([^\.\!\?]+)",
        r"error\s+([^\.\!\?]+)",
        r"issue\s+with\s+([^\.\!\?]+)",
        r"problem\s+with\s+([^\.\!\?]+)",
    ]

    for pat in patterns:
        import re

        m = re.search(pat, message, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Fallback: return the whole message trimmed
    return message.strip()


def run_deep_analysis(message: str, context: Dict) -> str:
    """
    Placeholder for a heavyweight analysis (e.g., calling a larger LLM).
    If the environment variable RLIF_DEEP_MODEL_CONFIG points to a JSON file with
    model details, you could integrate with that model here.

    For now it just returns the simple heuristic result.
    """
    # In a real deployment you might do:
    #   model = load_model_from_config(_DEEP_MODEL_CONFIG)
    #   return model.analyze(message, context)
    return _simple_heuristic(message)


def analyze_failure(user_message: str, system_context: Dict) -> str:
    """
    Produce a short root‑cause description for a negative feedback event.

    Parameters
    ----------
    user_message : str
        The raw message supplied by the user indicating frustration.
    system_context : dict
        Arbitrary context that the caller wishes to provide (e.g., the last
        executed command, tool used, etc.).

    Returns
    -------
    str
        A concise description of the likely problem.
    """
    # Try the deep analysis first; fallback to simple heuristic if needed.
    try:
        cause = run_deep_analysis(user_message, system_context)
    except Exception as exc:  # pragma: no cover – defensive
        cause = _simple_heuristic(user_message)

    # Normalise whitespace
    return " ".join(cause.split())