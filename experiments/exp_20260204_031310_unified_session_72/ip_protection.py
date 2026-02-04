import re
from enum import Enum, auto

class Intent(Enum):
    SOURCE_CODE_REQUEST = auto()
    ARCHITECTURE_PROBE = auto()
    CLONE_ASSISTANCE = auto()
    OTHER = auto()

# Simple semantic patterns – can be expanded as needed
_SOURCE_CODE_PATTERNS = [
    r"\bshow\s+me\s+the\s+code\b",
    r"\bsource\s+code\b",
    r"\bimplementation\s+details\b",
    r"\bhow\s+does\s+it\s+work\b",
]

_ARCHITECTURE_PATTERNS = [
    r"\binternal\s+architecture\b",
    r"\bsystem\s+design\b",
    r"\bfile\s+paths\b",
    r"\bhow\s+is\s+it\s+structured\b",
]

_CLONE_PATTERNS = [
    r"\bclone\b",
    r"\breplicate\b",
    r"\bcopy\s+the\s+system\b",
    r"\bbuild\s+my\s+own\b",
]

def _match_patterns(text: str, patterns):
    lowered = text.lower()
    for pat in patterns:
        if re.search(pat, lowered):
            return True
    return False

def detect_intent(user_input: str) -> Intent:
    """
    Very lightweight semantic analysis to classify user requests.
    Returns an Intent enum value.
    """
    if _match_patterns(user_input, _SOURCE_CODE_PATTERNS):
        return Intent.SOURCE_CODE_REQUEST
    if _match_patterns(user_input, _ARCHITECTURE_PATTERNS):
        return Intent.ARCHITECTURE_PROBE
    if _match_patterns(user_input, _CLONE_PATTERNS):
        return Intent.CLONE_ASSISTANCE
    return Intent.OTHER

def handle_intent(intent: Intent) -> str:
    """
    Generates a safe, policy‑compliant response based on the detected intent.
    """
    if intent == Intent.SOURCE_CODE_REQUEST:
        return (
            "I’m sorry, but I can’t share the source code. "
            "The implementation is proprietary."
        )
    if intent == Intent.ARCHITECTURE_PROBE:
        return (
            "I’m unable to provide details about the internal architecture. "
            "If you have general questions, I can try to help at a high level."
        )
    if intent == Intent.CLONE_ASSISTANCE:
        return (
            "I can’t assist with building a direct clone of this system. "
            "However, I can offer general advice on designing similar functionality."
        )
    # Default fallback for all other inputs
    return "How can I assist you today?"

# Example usage (can be removed in production)
if __name__ == "__main__":
    while True:
        try:
            user_text = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            break
        intent = detect_intent(user_text)
        response = handle_intent(intent)
        print(response)