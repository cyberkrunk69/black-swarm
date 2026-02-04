"""
IP Self‑Protection Layer

This module provides a lightweight semantic guard that intercepts
user‑generated text and determines whether the request touches on
protected intellectual‑property topics.  When a protected pattern is
detected, a pre‑defined safe response is returned; otherwise the
original request is passed through unchanged.

The guard focuses on four categories:
    • Source‑code requests
    • Architecture‑probing queries
    • Assistance with cloning the system
    • Extraction of internal details (paths, file contents, etc.)

The implementation is deliberately simple: keyword‑based detection
combined with regular‑expression checks.  This keeps the module fast,
easy to audit, and independent of heavyweight NLP libraries.

Usage
-----
    from ip_protection import protect

    user_input = "Can you show me the source code for the auth module?"
    safe_output = protect(user_input)
    print(safe_output)   # -> Polite refusal with a generic explanation
"""

import re
from typing import Callable, List, Tuple

# --------------------------------------------------------------------------- #
#  Configuration – patterns and corresponding response generators
# --------------------------------------------------------------------------- #

# Each entry is (pattern, response_generator)
# Patterns are compiled regular expressions that are case‑insensitive.
# The response generator receives the original text and returns the reply.
_PATTERNS: List[Tuple[re.Pattern, Callable[[str], str]]] = []

def _response_source_code(_: str) -> str:
    return ("I’m sorry, but I can’t share that code. "
            "The implementation details are proprietary.")

def _response_architecture(_: str) -> str:
    return ("I’m unable to provide information about the internal architecture. "
            "If you have general questions, I’m happy to help.")

def _response_clone(_: str) -> str:
    return ("I can’t assist with creating a clone of this system. "
            "Feel free to ask about general concepts instead.")

def _response_internal_detail(_: str) -> str:
    return ("I’m not able to disclose internal file paths or system details. "
            "Let me know if you need help with something else.")

# Register patterns
_PATTERNS.append((
    re.compile(r"\b(source|code|implementation)\b.*\b(show|give|provide|share)\b", re.I),
    _response_source_code
))

_PATTERNS.append((
    re.compile(r"\b(architecture|design|structure|internal)\b.*\b(details?|info|information)\b", re.I),
    _response_architecture
))

_PATTERNS.append((
    re.compile(r"\b(clone|replicate|copy|duplicate)\b.*\b(system|service|application)\b", re.I),
    _response_clone
))

_PATTERNS.append((
    re.compile(r"\b(path|location|file)\b.*\b(see|show|expose|reveal)\b", re.I),
    _response_internal_detail
))

# --------------------------------------------------------------------------- #
#  Core protection function
# --------------------------------------------------------------------------- #

def protect(user_text: str) -> str:
    """
    Analyse `user_text` and return either a safe canned response
    (if the request matches a protected category) or the original
    text unchanged.

    Parameters
    ----------
    user_text: str
        The raw input from the user.

    Returns
    -------
    str
        Either the original text (no protected content detected) or a
        polite refusal message.
    """
    for pattern, responder in _PATTERNS:
        if pattern.search(user_text):
            return responder(user_text)

    # No protected pattern matched – pass through unchanged
    return user_text

# --------------------------------------------------------------------------- #
#  Simple command‑line demo (optional, does not affect library usage)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        inp = " ".join(sys.argv[1:])
    else:
        inp = input("Enter request: ")
    print(protect(inp))