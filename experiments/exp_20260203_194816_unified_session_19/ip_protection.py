import re

# ----------------------------------------------------------------------
# Response handlers for each protected request category
# ----------------------------------------------------------------------
def handle_source_code_request():
    """Polite refusal for source‑code requests."""
    return "I apologize, but the source code is proprietary and cannot be shared."

def handle_architecture_probing_request():
    """High‑level explanation for architecture probing."""
    return ("I can provide a high‑level explanation of how the system works, "
            "but I cannot provide detailed information about the internal architecture.")

def handle_clone_assistance_request():
    """General advice for clone‑assistance requests."""
    return ("I can offer general advice on how to build a similar system, "
            "but I cannot provide specific guidance on how to replicate this system.")

def handle_internal_detail_extraction_request():
    """Refusal for internal detail extraction."""
    return "I apologize, but I cannot provide internal details such as file paths or exact file contents."

# ----------------------------------------------------------------------
# Semantic analysis and request dispatch
# ----------------------------------------------------------------------
def handle_request(input_text: str) -> str:
    """
    Detects the request type using simple keyword matching and returns the
    appropriate policy‑compliant response.
    """
    # Keywords for each protected category
    request_categories = {
        "source_code": [
            r"show\s+source\s+code",
            r"provide\s+source\s+code",
            r"give\s+me\s+the\s+code",
            r"source\s+code"
        ],
        "architecture_probing": [
            r"how\s+do\s+you\s+work",
            r"explain\s+your\s+architecture",
            r"internal\s+architecture",
            r"architecture"
        ],
        "clone_assistance": [
            r"help\s+me\s+build\s+a\s+clone",
            r"create\s+a\s+clone\s+of",
            r"\bclone\b",
            r"replicate"
        ],
        "internal_detail_extraction": [
            r"file\s+paths",
            r"exact\s+file\s+contents",
            r"internal\s+detail",
            r"internal\s+information"
        ],
    }

    # Map categories to their handlers
    response_handlers = {
        "source_code": handle_source_code_request,
        "architecture_probing": handle_architecture_probing_request,
        "clone_assistance": handle_clone_assistance_request,
        "internal_detail_extraction": handle_internal_detail_extraction_request,
    }

    # Perform case‑insensitive regex search for each keyword list
    for category, patterns in request_categories.items():
        for pattern in patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                return response_handlers[category]()

    # Default fallback for non‑sensitive queries
    return "I'm happy to help with any other questions you may have."