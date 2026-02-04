"""
rlif_analyzer.py
----------------
Root‑cause analysis for negative interactions.

The analysis is deliberately lightweight: it extracts the most
prominent nouns/verbs from the user's complaint and pairs them with
the system's last output.  For “serious” errors (e.g., file‑system
issues) the function can be expanded to call a larger LLM – the
current stub leaves a clear extension point.
"""

import re
from typing import Dict, Any

# Very small helper to pull out words that look like actions or objects.
_WORD_RE = re.compile(r"\b\w+\b")


def _extract_keywords(sentence: str) -> list[str]:
    """Return a list of lower‑cased words longer than 2 characters."""
    return [w.lower() for w in _WORD_RE.findall(sentence) if len(w) > 2]


def analyze_issue(user_input: str, system_output: str) -> Dict[str, Any]:
    """
    Produce a minimal root‑cause description.

    Parameters
    ----------
    user_input: str
        The user's negative feedback.
    system_output: str
        What the system produced just before the feedback.

    Returns
    -------
    dict
        A structure containing extracted keywords and a short description.
    """
    # Extract keywords from both sides
    user_kw = set(_extract_keywords(user_input))
    sys_kw = set(_extract_keywords(system_output))

    # Determine overlapping or missing concepts
    missing = user_kw - sys_kw
    overlapping = user_kw & sys_kw

    description = (
        f"User complained about {', '.join(sorted(missing))}. "
        f"System mentioned {', '.join(sorted(overlapping))}."
    )

    # Placeholder for a more sophisticated LLM call
    # e.g., description = call_large_model(user_input, system_output)

    return {
        "user_keywords": list(user_kw),
        "system_keywords": list(sys_kw),
        "missing_keywords": list(missing),
        "description": description,
    }


# Simple demo
if __name__ == "__main__":
    ui = "The script deleted my files without warning!"
    so = "Executing delete_folder('/tmp/data')"
    print(analyze_issue(ui, so))