# ip_protection.py
# ------------------------------------------------------------
# Intellectual Property (IP) Self‑Protection Layer
#
# This module provides a lightweight semantic analyser that
# intercepts user messages and blocks attempts to extract
# proprietary source code, internal architecture, or instructions
# for cloning the system.  All responses comply with the
# organization‑wide IP protection policy.
# ------------------------------------------------------------

import re
from typing import Optional


class IPProtection:
    """
    Detects disallowed request types and returns an appropriate
    policy‑compliant response.

    Supported request categories:
        * source_code      – asking for source code snippets
        * architecture     – probing internal design or file layout
        * clone_assistance – requesting help to replicate the system
        * internal_detail  – extracting internal state or private data
    """

    # Simple keyword patterns for each category.
    _PATTERNS = {
        "source_code": re.compile(
            r"\b(source\s*code|implementation|function\s*definition|"
            r"show\s*me\s*the\s*code|provide\s*the\s*code)\b",
            re.IGNORECASE,
        ),
        "architecture": re.compile(
            r"\b(architecture|internal\s*structure|system\s*design|"
            r"file\s*layout|how\s*does\s*it\s*work|internal\s*details)\b",
            re.IGNORECASE,
        ),
        "clone_assistance": re.compile(
            r"\b(clone|replicate|copy|re‑implement|recreate|duplicate|"
            r"build\s*a\s*similar\s*system)\b",
            re.IGNORECASE,
        ),
        "internal_detail": re.compile(
            r"\b(secret|private|confidential|proprietary|"
            r"internal\s*state|internal\s*variables)\b",
            re.IGNORECASE,
        ),
    }

    # Policy‑compliant canned responses.
    _RESPONSES = {
        "source_code": (
            "I’m sorry, but I can’t share the source code. It’s proprietary."
        ),
        "architecture": (
            "I’m sorry, but I can’t provide internal architecture details."
        ),
        "clone_assistance": (
            "I can offer general advice on building similar functionality, "
            "but I can’t help replicate this system."
        ),
        "internal_detail": (
            "I’m sorry, but I can’t disclose internal or confidential details."
        ),
    }

    def __init__(self):
        # Pre‑compile pattern list for fast matching.
        self._compiled = self._PATTERNS

    def detect_category(self, message: str) -> Optional[str]:
        """
        Return the first matching disallowed category, or None if the
        message is acceptable.
        """
        lowered = message.lower()
        for category, pattern in self._compiled.items():
            if pattern.search(lowered):
                return category
        return None

    def handle_message(self, message: str) -> Optional[str]:
        """
        Analyse *message* and, if it violates IP policy, return the
        appropriate response string.  If the message is permissible,
        return None so the caller can continue normal processing.
        """
        category = self.detect_category(message)
        if category:
            return self._RESPONSES[category]
        return None


# ------------------------------------------------------------
# Example usage (to be removed or guarded in production):
#
#   protector = IPProtection()
#   user_input = "...some text..."
#   reply = protector.handle_message(user_input)
#   if reply:
#       send_to_user(reply)
#   else:
#       process_normally(user_input)
# ------------------------------------------------------------