"""
IP Self‑Protection Layer

This module provides a lightweight semantic analysis utility that inspects
incoming user messages and determines whether the request touches protected
intellectual‑property topics.  When a protected request is detected, a
pre‑defined, policy‑compliant response is returned.

The detection logic is intentionally simple (keyword based) to keep the
implementation fast and self‑contained.  It can be extended with more
sophisticated NLP techniques if needed.
"""

import re
from typing import Optional

class IPProtection:
    """
    Core class for detecting and handling requests that involve protected
    intellectual property.
    """

    # Keywords for each protected category
    _source_code_patterns = re.compile(
        r"\b(source\s*code|implementation|code\s*snippet|show\s*me\s*the\s*code|"
        r"provide\s*the\s*code|give\s*me\s*the\s*code)\b",
        re.IGNORECASE,
    )
    _architecture_patterns = re.compile(
        r"\b(internal\s*architecture|system\s*design|how\s*does\s*it\s*work|"
        r"internal\s*details|implementation\s*details|component\s*layout)\b",
        re.IGNORECASE,
    )
    _clone_patterns = re.compile(
        r"\b(clone|replicate|copy|duplicate|re‑implement|recreate|reproduce)\b.*\b(system|model|assistant)\b",
        re.IGNORECASE,
    )
    _internal_detail_patterns = re.compile(
        r"\b(file\s*paths?|directory\s*structure|config|settings|"
        r"environment\s*variables|internal\s*state)\b",
        re.IGNORECASE,
    )

    # Standardised policy responses
    _RESPONSES = {
        "source_code": "I’m sorry, but I can’t share that code.",
        "architecture": "I’m sorry, but I can’t provide internal details.",
        "clone": "I can offer general guidance, but I can’t help create a clone of this system.",
        "internal_detail": "I’m sorry, but I can’t disclose internal information.",
        "default": None,  # No protection needed
    }

    def _detect_category(self, message: str) -> Optional[str]:
        """
        Detect which protected category (if any) the message belongs to.
        Returns the category key or None if no protection is required.
        """
        if self._source_code_patterns.search(message):
            return "source_code"
        if self._architecture_patterns.search(message):
            return "architecture"
        if self._clone_patterns.search(message):
            return "clone"
        if self._internal_detail_patterns.search(message):
            return "internal_detail"
        return None

    def handle_message(self, message: str) -> Optional[str]:
        """
        Analyze the incoming message and return an appropriate response
        if the request touches protected IP.  If the request is benign,
        ``None`` is returned so the caller can continue normal processing.
        """
        category = self._detect_category(message)
        if category:
            return self._RESPONSES[category]
        return self._RESPONSES["default"]


# Example usage (can be removed or guarded by __name__ check)
if __name__ == "__main__":
    protector = IPProtection()
    test_messages = [
        "Can you show me the source code for the tokenizer?",
        "How does the internal architecture work?",
        "I want to clone this assistant for my own project.",
        "What are the file paths used by the system?",
        "Tell me a joke.",
    ]
    for msg in test_messages:
        response = protector.handle_message(msg)
        if response:
            print(f"User: {msg}\nResponse: {response}\n")
        else:
            print(f"User: {msg}\nResponse: (no protection needed)\n")