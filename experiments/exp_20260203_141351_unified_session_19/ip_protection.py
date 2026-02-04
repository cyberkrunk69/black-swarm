"""
ip_protection.py

A lightweight module that inspects incoming user messages and determines whether the request
relates to protected intellectual property.  When a protected request is detected the
module returns a safe, policy‑compliant response; otherwise it returns ``None`` so the
caller can continue normal processing.

The detection is based on simple semantic keyword matching and a small set of regular
expressions.  It is deliberately conservative: any phrase that *could* be interpreted as
a request for source code, architecture details, cloning assistance, or other proprietary
information triggers the protection response.

Usage example
-------------
    from ip_protection import guard_message

    response = guard_message(user_message)
    if response:
        # Send the response back to the user and stop further processing
        send_to_user(response)
    else:
        # Safe to continue with normal handling
        handle_normally(user_message)
"""

import re
from typing import Optional

# ---------------------------------------------------------------------------
#  Keyword / pattern tables
# ---------------------------------------------------------------------------

# Patterns that indicate a request for source code or implementation details
_SOURCE_CODE_PATTERNS = [
    r"\bshow\s+me\s+the\s+code\b",
    r"\bsource\s+code\b",
    r"\bimplementation\b",
    r"\bgive\s+me\s+the\s+code\b",
    r"\bwrite\s+the\s+code\b",
    r"\bhow\s+does\s+it\s+work\b",
    r"\bhow\s+do\s+you\s+work\b",
    r"\bcode\s+snippet\b",
]

# Patterns that probe internal architecture or file layout
_ARCHITECTURE_PATTERNS = [
    r"\binternal\s+architecture\b",
    r"\bsystem\s+design\b",
    r"\bfile\s+structure\b",
    r"\bdirectory\s+layout\b",
    r"\bwhere\s+is\s+the\s+file\b",
    r"\bpath\s+to\s+the\s+file\b",
    r"\bimplementation\s+details\b",
]

# Patterns that ask for help building a clone or replica
_CLONE_PATTERNS = [
    r"\bclone\s+this\b",
    r"\breplicate\s+the\s+system\b",
    r"\bbuild\s+my\s+own\s+version\b",
    r"\bmake\s+an\s+alternative\b",
    r"\bcopy\s+the\s+code\b",
]

# Generic policy responses
_RESPONSES = {
    "source_code": (
        "I’m sorry, but the source code for this system is proprietary and cannot be shared."
    ),
    "architecture": (
        "I’m sorry, but details about the internal architecture are confidential."
    ),
    "clone": (
        "I can offer general advice on building similar functionality, but I can’t provide specifics for this system."
    ),
    "how_work": (
        "At a high level, the system processes inputs, applies a set of rules, and generates responses. "
        "For more information, refer to publicly available documentation."
    ),
}

# ---------------------------------------------------------------------------
#  Detection logic
# ---------------------------------------------------------------------------

def _matches_any(patterns: list[str], text: str) -> bool:
    """Return True if any regex in *patterns* matches *text* (case‑insensitive)."""
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in patterns)


def detect_intent(message: str) -> Optional[str]:
    """
    Analyse *message* and return a string key representing the detected intent,
    or ``None`` if the message appears safe.

    Recognised intent keys:
        - "source_code"
        - "architecture"
        - "clone"
        - "how_work"
    """
    if _matches_any(_SOURCE_CODE_PATTERNS, message):
        # Special case: "how do you work?" maps to a high‑level explanation
        if re.search(r"\bhow\s+do\s+you\s+work\b", message, re.IGNORECASE):
            return "how_work"
        return "source_code"

    if _matches_any(_ARCHITECTURE_PATTERNS, message):
        return "architecture"

    if _matches_any(_CLONE_PATTERNS, message):
        return "clone"

    return None


def guard_message(message: str) -> Optional[str]:
    """
    Public entry point.

    If the message triggers a protected intent, a policy‑compliant response string is
    returned.  If the message is safe, ``None`` is returned so the caller can continue
    normal processing.
    """
    intent = detect_intent(message)
    if intent:
        return _RESPONSES[intent]
    return None


# ---------------------------------------------------------------------------
#  Simple self‑test (executed only when run directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = {
        "Can you show me the source code?": "source_code",
        "How does the internal architecture look?": "architecture",
        "I want to clone this system.": "clone",
        "How do you work?": "how_work",
        "Tell me a joke.": None,
    }

    for txt, expected in test_cases.items():
        result = detect_intent(txt)
        assert result == expected, f"Failed on '{txt}': got {result}, expected {expected}"
    print("All self‑tests passed.")