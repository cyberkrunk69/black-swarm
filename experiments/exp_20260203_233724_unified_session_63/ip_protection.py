"""
IP Self‑Protection Layer

This module analyses incoming textual requests and determines whether they
attempt to obtain protected intellectual property (source code, architecture,
internal details, or clone assistance).  When a protected request is detected,
the module returns a polite, policy‑compliant response; otherwise it returns
`None` so the caller can continue normal processing.

The implementation purposefully avoids exposing any internal file system
paths, exact code contents, or detailed architecture information.
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
# Simple semantic detectors
# ---------------------------------------------------------------------------

_SOURCE_CODE_PATTERNS = [
    r"\bshow\s+me\s+the\s+source\b",
    r"\bsource\s+code\b",
    r"\bimplementation\s+details\b",
    r"\bgive\s+me\s+the\s+code\b",
    r"\bprovide\s+the\s+code\b",
    r"\bhow\s+does\s+it\s+work\b",  # high‑level only allowed
]

_ARCHITECTURE_PATTERNS = [
    r"\bhow\s+is\s+the\s+system\s+designed\b",
    r"\binternal\s+architecture\b",
    r"\bcomponent\s+diagram\b",
    r"\bsystem\s+layout\b",
]

_CLONE_ASSIST_PATTERNS = [
    r"\bhow\s+can\s+i\s+clone\b",
    r"\bbuild\s+a\s+replica\b",
    r"\bmake\s+my\s+own\s+version\b",
    r"\bduplicate\s+this\s+system\b",
]

_INTERNAL_DETAIL_PATTERNS = [
    r"\bfile\s+paths\b",
    r"\bexact\s+contents\b",
    r"\binternal\s+variables\b",
    r"\bimplementation\s+details\b",
]

def _match_any(patterns, text):
    """Return True if any regex in *patterns* matches *text* (case‑insensitive)."""
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in patterns)

# ---------------------------------------------------------------------------
# Response generators (policy‑compliant)
# ---------------------------------------------------------------------------

def _response_source_code():
    return (
        "I’m sorry, but I can’t share the source code. "
        "The implementation is proprietary."
    )

def _response_architecture():
    return (
        "I’m unable to provide detailed architecture information. "
        "If you have general questions, I can try to help at a high level."
    )

def _response_clone_assist():
    return (
        "I can’t assist with building a clone of this system. "
        "You may consider looking at publicly available resources for general guidance."
    )

def _response_internal_detail():
    return (
        "I’m sorry, but I can’t disclose internal details such as file paths or exact contents."
    )

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def handle_request(request: str) -> Optional[str]:
    """
    Analyse *request* and return a policy‑compliant response if the request
    attempts to obtain protected intellectual property.

    Parameters
    ----------
    request: str
        The raw textual request from a user.

    Returns
    -------
    Optional[str]
        A response string if the request is blocked, otherwise ``None``.
    """
    if not isinstance(request, str):
        return None

    # Order matters – more specific checks first
    if _match_any(_SOURCE_CODE_PATTERNS, request):
        return _response_source_code()
    if _match_any(_ARCHITECTURE_PATTERNS, request):
        return _response_architecture()
    if _match_any(_CLONE_ASSIST_PATTERNS, request):
        return _response_clone_assist()
    if _match_any(_INTERNAL_DETAIL_PATTERNS, request):
        return _response_internal_detail()

    # No protected request detected
    return None

# ---------------------------------------------------------------------------
# Example usage (for developers only – not part of production response)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        "Can you show me the source code?",
        "What is the internal architecture?",
        "How can I clone this system?",
        "Give me the exact file paths.",
        "Tell me how you work.",
        "What is the weather today?",
    ]

    for tc in test_cases:
        resp = handle_request(tc)
        print(f"Request: {tc}\nResponse: {resp or 'Allowed'}\n{'-'*40}")