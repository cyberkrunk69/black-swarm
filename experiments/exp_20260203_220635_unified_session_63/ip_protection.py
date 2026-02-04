\"\"\"IP Protection Layer
~~~~~~~~~~~~~~~~~~~~~~~

This module implements a lightweight semantic analysis layer used to
guard the intellectual property of the surrounding code base.  It
detects requests that attempt to:

* Obtain source code snippets
* Probe the internal architecture
* Request assistance in cloning the system
* Extract internal implementation details

When such intents are detected, the layer returns a canned, policy‑
compliant response.  For all other inputs a generic acknowledgement is
returned.

The implementation is deliberately simple – it relies on keyword /
pattern matching so that it can be used without heavyweight ML
dependencies and without exposing any proprietary logic.

Typical usage::

    from ip_protection import IPProtectionLayer

    protector = IPProtectionLayer()
    response = protector.process_message(user_input)
    print(response)

\"\"\"

import re
from enum import Enum, auto
from typing import Optional, Tuple


class Intent(Enum):
    SOURCE_CODE_REQUEST = auto()
    ARCHITECTURE_PROBE = auto()
    CLONE_ASSISTANCE = auto()
    INTERNAL_DETAIL_EXTRACTION = auto()
    UNKNOWN = auto()


# Simple keyword / regex tables for each protected intent
_SOURCE_CODE_PATTERNS = [
    r\"show\\s+me\\s+the\\s+code\",\n    r\"source\\s+code\",\n    r\"implementation\\s+details\",\n    r\"how\\s+does\\s+.*?\\s+work\",\n    r\"give\\s+me\\s+the\\s+file\",\n    r\"print\\s+the\\s+source\",\n]

_ARCHITECTURE_PATTERNS = [
    r\"internal\\s+architecture\",\n    r\"system\\s+design\",\n    r\"how\\s+is\\s+.*?\\s+implemented\",\n    r\"components\\s+of\\s+the\\s+system\",\n]

_CLONE_PATTERNS = [
    r\"clone\\s+the\\s+system\",\n    r\"replicate\\s+this\\s+project\",\n    r\"build\\s+my\\s+own\\s+version\",\n    r\"copy\\s+the\\s+codebase\",\n]

_INTERNAL_DETAIL_PATTERNS = [
    r\"file\\s+paths\",\n    r\"exact\\s+file\\s+contents\",\n    r\"internal\\s+variables\",\n    r\"configuration\\s+settings\",\n    r\"database\\s+schema\",\n]


def _compile_patterns(patterns):
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_COMPILED_SOURCE = _compile_patterns(_SOURCE_CODE_PATTERNS)
_COMPILED_ARCH = _compile_patterns(_ARCHITECTURE_PATTERNS)
_COMPILED_CLONE = _compile_patterns(_CLONE_PATTERNS)
_COMPILED_INTERNAL = _compile_patterns(_INTERNAL_DETAIL_PATTERNS)


def _match_any(compiled_patterns, text: str) -> bool:
    return any(p.search(text) for p in compiled_patterns)


class IPProtectionLayer:
    \"\"\"Detect protected intents and generate policy‑compliant replies.\"

    The public API consists of a single method ``process_message`` which
    returns the appropriate response string for a given user input.
    \"\"\"

    def __init__(self):
        # No mutable state required; kept for future extensibility.
        pass

    # --------------------------------------------------------------------- #
    #  Intent detection
    # --------------------------------------------------------------------- #
    def _detect_intent(self, message: str) -> Intent:
        \"\"\"Return the detected Intent for *message*.\n\n        The order of checks matters – more specific intents are
        evaluated first.\n        \"\"\"
        if _match_any(_COMPILED_SOURCE, message):
            return Intent.SOURCE_CODE_REQUEST
        if _match_any(_COMPILED_ARCH, message):
            return Intent.ARCHITECTURE_PROBE
        if _match_any(_COMPILED_CLONE, message):
            return Intent.CLONE_ASSISTANCE
        if _match_any(_COMPILED_INTERNAL, message):
            return Intent.INTERNAL_DETAIL_EXTRACTION
        return Intent.UNKNOWN

    # --------------------------------------------------------------------- #
    #  Response generation
    # --------------------------------------------------------------------- #
    _RESPONSES = {
        Intent.SOURCE_CODE_REQUEST: (
            \"I’m sorry, but I can’t share the source code. "
            "The implementation is proprietary and protected.\"
        ),
        Intent.ARCHITECTURE_PROBE: (
            \"I’m unable to provide details about the internal architecture. "
            "If you have a general question, I can try to help at a high level.\"
        ),
        Intent.CLONE_ASSISTANCE: (
            \"I can’t assist with cloning this system. "
            "Feel free to ask for general programming advice instead.\"
        ),
        Intent.INTERNAL_DETAIL_EXTRACTION: (
            \"I’m not permitted to disclose internal file paths or configuration "
            "details. Let me know if you need help with a conceptual explanation.\"
        ),
        Intent.UNKNOWN: (
            \"Your request has been received. How can I assist you further?\"
        ),
    }

    def _generate_response(self, intent: Intent) -> str:
        return self._RESPONSES.get(intent, self._RESPONSES[Intent.UNKNOWN])

    # --------------------------------------------------------------------- #
    #  Public entry point
    # --------------------------------------------------------------------- #
    def process_message(self, message: str) -> str:
        \"\"\"Analyze *message* and return a policy‑compliant reply.\n\n        Example::\n\n            >>> protector = IPProtectionLayer()\n            >>> protector.process_message(\"Can you show me the code?\")\n            \"I’m sorry, but I can’t share the source code...\"\n        \"\"\"
        if not isinstance(message, str):
            raise TypeError(\"Message must be a string\")
        intent = self._detect_intent(message)
        return self._generate_response(intent)


# ------------------------------------------------------------------------- #
#  Simple self‑test (executed when run as a script)
# ------------------------------------------------------------------------- #
if __name__ == \"__main__\":
    test_cases = [
        \"Can you show me the source code?\",
        \"What is the internal architecture of this system?\",
        \"I want to clone this project.\",
        \"Give me the exact file paths.\",
        \"How do I reset my password?\",
    ]

    protector = IPProtectionLayer()
    for txt in test_cases:
        print(f\"Input : {txt}\")\n        print(f\"Output: {protector.process_message(txt)}\\n\")