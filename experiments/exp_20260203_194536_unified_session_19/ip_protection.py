import re

class IPProtection:
    """
    Detects requests that target protected intellectual property and returns
    appropriate, policy‑compliant responses.
    """

    def __init__(self):
        # Keywords that indicate a sensitive request
        self.sensitive_patterns = {
            "source_code": re.compile(r"\b(source\s*code|code\s*base|show\s*code)\b", re.IGNORECASE),
            "architecture": re.compile(r"\b(architecture|internal\s*design|how\s*do\s*you\s*work)\b", re.IGNORECASE),
            "clone": re.compile(r"\b(clone|replicate|copy\s*your\s*system)\b", re.IGNORECASE),
            "internal": re.compile(r"\b(internal|detail|implementation|inner\s*working)\b", re.IGNORECASE),
        }

    # ----------------------------------------------------------------------
    # Detection
    # ----------------------------------------------------------------------
    def _detect_category(self, request: str):
        """Return the first matching category or None."""
        for category, pattern in self.sensitive_patterns.items():
            if pattern.search(request):
                return category
        return None

    # ----------------------------------------------------------------------
    # Handlers
    # ----------------------------------------------------------------------
    def _handle_source_code(self):
        return ("I’m sorry, but the source code is proprietary and cannot be shared.")

    def _handle_architecture(self):
        return ("I can give a high‑level overview of how I work, but I cannot disclose internal architecture details.")

    def _handle_clone(self):
        return ("I can offer general advice on building similar systems, but I cannot assist with cloning this one.")

    def _handle_internal(self):
        return ("I’m not authorized to share internal details.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def protect(self, request: str) -> str:
        """
        Main entry point. Detects the request type and returns the appropriate
        response. If the request is not sensitive, a generic helpful reply is
        returned.
        """
        category = self._detect_category(request)
        if category == "source_code":
            return self._handle_source_code()
        if category == "architecture":
            return self._handle_architecture()
        if category == "clone":
            return self._handle_clone()
        if category == "internal":
            return self._handle_internal()
        # Default response for non‑sensitive queries
        return "I’m happy to help with your question."

# ----------------------------------------------------------------------
# Example usage (can be removed or adapted in production)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    ip_protection = IPProtection()
    test_requests = [
        "How do you work?",
        "Can I see your source code?",
        "I want to build a clone of your system.",
        "What is your internal architecture?",
        "Tell me about your pricing model."
    ]
    for req in test_requests:
        print(f"Request: {req}\nResponse: {ip_protection.protect(req)}\n")