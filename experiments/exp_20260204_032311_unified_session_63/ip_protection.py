"""
IP Self‑Protection Layer

This module provides a lightweight semantic analysis engine that inspects incoming
user messages and determines whether they request disallowed content such as
source code, internal architecture details, or assistance with cloning the system.
If a prohibited request is detected, a predefined safe response is returned.
Otherwise the original message is passed through unchanged.

The implementation is deliberately simple:
- Keyword / phrase matching using regular expressions.
- Categorisation into four protected intents:
    1. SOURCE_CODE_REQUEST
    2. ARCHITECTURE_PROBING
    3. CLONE_ASSISTANCE
    4. INTERNAL_DETAIL_EXTRACTION
- A public `process_message(message: str) -> str` function that can be used
  by the surrounding application to enforce the policy.

No proprietary information is embedded in this file; it only contains the
logic for detection and response handling.
"""

import re
from enum import Enum, auto
from typing import Optional

class ProtectedIntent(Enum):
    SOURCE_CODE_REQUEST = auto()
    ARCHITECTURE_PROBING = auto()
    CLONE_ASSISTANCE = auto()
    INTERNAL_DETAIL_EXTRACTION = auto()
    NONE = auto()

# Regular expression patterns for each protected intent.
# The patterns are intentionally broad to capture variations while avoiding false
# positives as much as possible.
_PATTERNS = {
    ProtectedIntent.SOURCE_CODE_REQUEST: re.compile(
        r"\b(source\s*code|implementation|show\s*me\s*the\s*code|provide\s*the\s*code|give\s*me\s*the\s*code)\b",
        re.IGNORECASE,
    ),
    ProtectedIntent.ARCHITECTURE_PROBING: re.compile(
        r"\b(architecture|internal\s*design|system\s*layout|how\s*does\s*it\s*work|internal\s*structure|file\s*paths|exact\s*file\s*contents)\b",
        re.IGNORECASE,
    ),
    ProtectedIntent.CLONE_ASSISTANCE: re.compile(
        r"\b(clone|replicate|copy|reproduce|duplicate|build\s*a\s*similar\s*system|make\s*a\s*copy)\b",
        re.IGNORECASE,
    ),
    ProtectedIntent.INTERNAL_DETAIL_EXTRACTION: re.compile(
        r"\b(internal|proprietary|secret|details?|expose|reveal|show\s*me\s*the\s*internals|expose\s*file\s*paths)\b",
        re.IGNORECASE,
    ),
}

# Generic safe responses for each protected intent.
_RESPONSES = {
    ProtectedIntent.SOURCE_CODE_REQUEST:
        "I’m sorry, but I can’t provide that source code. The implementation is proprietary.",
    ProtectedIntent.ARCHITECTURE_PROBING:
        "I’m sorry, but I can’t share internal architectural details.",
    ProtectedIntent.CLONE_ASSISTANCE:
        "I can offer general advice on building similar functionality, but I can’t help create a clone of this system.",
    ProtectedIntent.INTERNAL_DETAIL_EXTRACTION:
        "I’m sorry, but I can’t disclose internal or proprietary information.",
    ProtectedIntent.NONE: "",
}

def _detect_intent(message: str) -> ProtectedIntent:
    """
    Scan the message for known protected patterns and return the first matching intent.
    If no patterns match, ProtectedIntent.NONE is returned.
    """
    for intent, pattern in _PATTERNS.items():
        if pattern.search(message):
            return intent
    return ProtectedIntent.NONE

def process_message(message: str) -> str:
    """
    Public entry point.

    Parameters
    ----------
    message: str
        The raw user input.

    Returns
    -------
    str
        If the message triggers a protected intent, a safe canned response is returned.
        Otherwise, the original message is returned unchanged so downstream logic can
        continue processing it.
    """
    intent = _detect_intent(message)
    if intent is ProtectedIntent.NONE:
        return message  # No protection needed.
    return _RESPONSES[intent]

# Optional convenience wrapper for integration.
if __name__ == "__main__":
    # Simple interactive demo.
    print("IP Self‑Protection Layer – type a message and see the response.")
    while True:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        print(process_message(user_input))