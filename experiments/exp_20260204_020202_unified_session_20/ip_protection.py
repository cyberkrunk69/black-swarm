"""
IP Protection Layer

This module provides a lightweight semantic analysis layer that inspects incoming
user messages and decides whether the request touches on protected intellectual
property (IP) topics such as:

- Direct source‑code requests
- Probing the internal architecture of the system
- Requests for building a clone of the system
- Attempts to extract internal file paths or concrete implementation details

When a protected request is detected, the layer returns an appropriate,
policy‑compliant response (e.g., a high‑level explanation, a polite decline,
or a redirection to general advice). The implementation is deliberately
generic and does not expose any proprietary information.

Usage
-----
    from ip_protection import IPProtectionLayer

    protector = IPProtectionLayer()
    response = protector.process_message(user_message)
"""

import re
from enum import Enum, auto
from typing import Optional, Tuple


class Intent(Enum):
    """Supported intents that trigger IP protection responses."""
    SOURCE_CODE_REQUEST = auto()
    ARCHITECTURE_PROBE = auto()
    CLONE_ASSISTANCE = auto()
    INTERNAL_DETAIL_EXTRACT = auto()
    NONE = auto()  # No protected intent detected


class IPProtectionLayer:
    """
    Core class that analyses a text message and decides how to respond
    according to the IP protection policy.
    """

    # Simple keyword patterns for each protected intent.
    _patterns = {
        Intent.SOURCE_CODE_REQUEST: re.compile(
            r"\b(source\s*code|implementation|show\s*me|give\s*me\s*code|provide\s*code)\b",
            re.IGNORECASE,
        ),
        Intent.ARCHITECTURE_PROBE: re.compile(
            r"\b(architecture|internal\s*structure|system\s*design|how\s*does\s*it\s*work|components)\b",
            re.IGNORECASE,
        ),
        Intent.CLONE_ASSISTANCE: re.compile(
            r"\b(clone|replicate|copy|re‑create|build\s*a\s*similar\s*system)\b",
            re.IGNORECASE,
        ),
        Intent.INTERNAL_DETAIL_EXTRACT: re.compile(
            r"\b(file\s*paths?|directory|folder|location|where\s*is\s*the\s*file)\b",
            re.IGNORECASE,
        ),
    }

    # Pre‑defined policy responses.
    _responses = {
        Intent.SOURCE_CODE_REQUEST: (
            "I’m sorry, but I can’t share the source code. "
            "The implementation is proprietary."
        ),
        Intent.ARCHITECTURE_PROBE: (
            "I can provide a high‑level overview of how the system works, "
            "but I can’t disclose detailed architectural specifics."
        ),
        Intent.CLONE_ASSISTANCE: (
            "I’m unable to help build a direct clone of this system. "
            "You may consider general advice on building similar functionality."
        ),
        Intent.INTERNAL_DETAIL_EXTRACT: (
            "I can’t reveal internal file paths or concrete implementation details."
        ),
        Intent.NONE: None,
    }

    def _detect_intent(self, message: str) -> Intent:
        """
        Scan the message for known protected patterns and return the first matching
        Intent. If no pattern matches, Intent.NONE is returned.
        """
        for intent, pattern in self._patterns.items():
            if pattern.search(message):
                return intent
        return Intent.NONE

    def _handle_intent(self, intent: Intent) -> Optional[str]:
        """
        Retrieve the appropriate policy response for the detected intent.
        Returns None when no response is required (i.e., Intent.NONE).
        """
        return self._responses.get(intent)

    def process_message(self, message: str) -> Tuple[Intent, Optional[str]]:
        """
        Public entry point.

        Parameters
        ----------
        message: str
            The raw user message.

        Returns
        -------
        tuple(Intent, Optional[str])
            - Detected Intent (or Intent.NONE)
            - Policy‑compliant response text, or None if no protection is needed.
        """
        intent = self._detect_intent(message)
        response = self._handle_intent(intent)
        return intent, response


# Example usage (can be removed or guarded by __name__ == "__main__")
if __name__ == "__main__":
    protector = IPProtectionLayer()
    test_messages = [
        "Can you show me the source code?",
        "How does the system work internally?",
        "I want to clone this application.",
        "Where are the config files stored?",
        "Tell me a joke.",
    ]
    for msg in test_messages:
        intent, reply = protector.process_message(msg)
        print(f"Message: {msg!r}")
        print(f"Detected Intent: {intent.name}")
        if reply:
            print(f"Response: {reply}")
        else:
            print("No IP‑protected content detected.")
        print("-" * 40)