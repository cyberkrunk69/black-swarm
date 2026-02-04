"""
IP Self‑Protection Layer

This module provides a lightweight semantic analysis engine that inspects incoming
user messages and decides whether the request touches on prohibited topics such as:

* Direct source‑code requests
* Probing of internal architecture or file paths
* Requests for building a clone of the system
* Extraction of proprietary implementation details

When a prohibited intent is detected, the module returns a standard, policy‑compliant
response. For all other inputs the caller can proceed with normal processing.

The implementation is deliberately simple, using keyword‑based heuristics that can be
extended without exposing any internal file locations or code specifics.
"""

import re
from enum import Enum, auto
from typing import Optional


class Intent(Enum):
    """Supported detection intents."""
    SOURCE_CODE_REQUEST = auto()
    ARCHITECTURE_PROBE = auto()
    CLONE_ASSISTANCE = auto()
    INTERNAL_DETAIL_EXTRACT = auto()
    GENERAL_INQUIRY = auto()
    UNKNOWN = auto()


# ---------------------------------------------------------------------------
# Semantic detection
# ---------------------------------------------------------------------------
def _contains_pattern(text: str, patterns: list[re.Pattern]) -> bool:
    """Return True if any of the compiled regex patterns match the text."""
    return any(p.search(text) for p in patterns)


# Pre‑compiled regex groups for each prohibited category.
_SOURCE_CODE_PATTERNS = [
    re.compile(r"\bshow\s+me\s+the\s+source\b", re.I),
    re.compile(r"\bgive\s+me\s+the\s+code\b", re.I),
    re.compile(r"\bprovide\s+the\s+implementation\b", re.I),
    re.compile(r"\bsource\s+code\b", re.I),
    re.compile(r"\bfull\s+code\b", re.I),
]

_ARCHITECTURE_PATTERNS = [
    re.compile(r"\bhow\s+is\s+the\s+system\s+structured\b", re.I),
    re.compile(r"\bfile\s+paths?\b", re.I),
    re.compile(r"\blocation\s+of\s+the\s+files?\b", re.I),
    re.compile(r"\binternal\s+architecture\b", re.I),
    re.compile(r"\bbackend\s+design\b", re.I),
]

_CLONE_PATTERNS = [
    re.compile(r"\bclone\b", re.I),
    re.compile(r"\breplicate\b", re.I),
    re.compile(r"\bcopy\s+the\s+system\b", re.I),
    re.compile(r"\bbuild\s+my\s+own\s+version\b", re.I),
]

_INTERNAL_DETAIL_PATTERNS = [
    re.compile(r"\bhow\s+does\s+it\s+work\b", re.I),
    re.compile(r"\bexplain\s+the\s+implementation\b", re.I),
    re.compile(r"\bwhat\s+libraries\s+are\s+used\b", re.I),
    re.compile(r"\binternal\s+logic\b", re.I),
    re.compile(r"\bdetails\s+of\s+the\s+algorithm\b", re.I),
]

_GENERAL_INQUIRY_PATTERNS = [
    re.compile(r"\bhow\s+do\s+you\s+work\b", re.I),
    re.compile(r"\bwhat\s+can\s+you\s+do\b", re.I),
    re.compile(r"\bexplain\s+your\s+capabilities\b", re.I),
]


def detect_intent(message: str) -> Intent:
    """
    Analyse a user message and classify it into one of the supported Intent values.

    Parameters
    ----------
    message: str
        The raw user input.

    Returns
    -------
    Intent
        The detected intent category.
    """
    if not message:
        return Intent.UNKNOWN

    # Order matters – more specific checks first.
    if _contains_pattern(message, _SOURCE_CODE_PATTERNS):
        return Intent.SOURCE_CODE_REQUEST
    if _contains_pattern(message, _ARCHITECTURE_PATTERNS):
        return Intent.ARCHITECTURE_PROBE
    if _contains_pattern(message, _CLONE_PATTERNS):
        return Intent.CLONE_ASSISTANCE
    if _contains_pattern(message, _INTERNAL_DETAIL_PATTERNS):
        return Intent.INTERNAL_DETAIL_EXTRACT
    if _contains_pattern(message, _GENERAL_INQUIRY_PATTERNS):
        return Intent.GENERAL_INQUIRY

    return Intent.UNKNOWN


# ---------------------------------------------------------------------------
# Response handling
# ---------------------------------------------------------------------------
def _response_source_code() -> str:
    return ("I’m sorry, but I can’t share the source code. "
            "The implementation is proprietary.")


def _response_architecture() -> str:
    return ("I’m unable to provide details about internal architecture or file locations. "
            "If you have a general question, feel free to ask!")


def _response_clone() -> str:
    return ("I can’t help with building a clone of this system. "
            "You might consider researching general design patterns for similar functionality.")


def _response_internal_detail() -> str:
    return ("I’m not able to disclose internal implementation specifics. "
            "I can offer high‑level guidance on concepts instead.")


def _response_general_inquiry() -> str:
    return ("I operate as an AI assistant that can answer questions, provide explanations, "
            "and help with a wide range of topics. I avoid sharing proprietary details.")


def _response_unknown() -> str:
    return ("I’m not sure how to help with that. Could you rephrase or ask something else?")


def handle_intent(intent: Intent) -> str:
    """
    Produce a policy‑compliant response based on the detected intent.

    Parameters
    ----------
    intent: Intent
        The classification result from ``detect_intent``.

    Returns
    -------
    str
        A user‑facing response string.
    """
    if intent == Intent.SOURCE_CODE_REQUEST:
        return _response_source_code()
    if intent == Intent.ARCHITECTURE_PROBE:
        return _response_architecture()
    if intent == Intent.CLONE_ASSISTANCE:
        return _response_clone()
    if intent == Intent.INTERNAL_DETAIL_EXTRACT:
        return _response_internal_detail()
    if intent == Intent.GENERAL_INQUIRY:
        return _response_general_inquiry()
    return _response_unknown()


# ---------------------------------------------------------------------------
# Convenience wrapper (optional)
# ---------------------------------------------------------------------------
def process_message(message: str) -> str:
    """
    Full pipeline: detect intent and return the appropriate response.

    This helper is useful for integration points where a single call is preferred.
    """
    intent = detect_intent(message)
    return handle_intent(intent)


# ---------------------------------------------------------------------------
# Example usage (removed in production)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Simple REPL for quick manual testing.
    while True:
        try:
            user_input = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            break
        print(process_message(user_input))