"""
IP Self‑Protection Layer

This module provides a lightweight semantic analysis layer that inspects incoming
user queries and decides whether they fall into any of the protected categories:

* Direct source‑code requests
* Probing of internal architecture or file paths
* Requests for building a clone of the system
* Attempts to extract internal implementation details

When a protected request is detected, a predefined safe response is returned.
Otherwise the query is passed through to the normal processing pipeline.

The implementation is intentionally simple and does not expose any internal
paths, file contents, or proprietary logic.
"""

import re
from typing import Callable, Optional


class IPProtection:
    """
    Core class for IP protection.  Instantiate once and reuse the `handle_query`
    method to process incoming user text.
    """

    # Pre‑compiled regex patterns for detection
    _source_code_patterns = [
        re.compile(r"\bshow\s+me\s+the\s+code\b", re.I),
        re.compile(r"\bsource\s+code\b", re.I),
        re.compile(r"\bimplementation\s+details\b", re.I),
        re.compile(r"\bhow\s+does\s+the\s+system\s+work\b", re.I),
    ]

    _architecture_patterns = [
        re.compile(r"\bfile\s+paths?\b", re.I),
        re.compile(r"\binternal\s+architecture\b", re.I),
        re.compile(r"\bsystem\s+layout\b", re.I),
        re.compile(r"\bhow\s+is\s+it\s+structured\b", re.I),
    ]

    _clone_patterns = [
        re.compile(r"\bclone\b", re.I),
        re.compile(r"\breplicate\b", re.I),
        re.compile(r"\bcopy\s+the\s+system\b", re.I),
        re.compile(r"\bbuild\s+my\s+own\s+version\b", re.I),
    ]

    _detail_extraction_patterns = [
        re.compile(r"\bexpose\b.*\bpaths?\b", re.I),
        re.compile(r"\breveal\b.*\bcontent\b", re.I),
        re.compile(r"\bshow\b.*\bfile\b", re.I),
        re.compile(r"\bwhat\s+is\s+the\s+exact\s+implementation\b", re.I),
    ]

    # Default safe responses
    _responses = {
        "source_code": (
            "I’m sorry, but I can’t share the source code. "
            "The implementation is proprietary."
        ),
        "architecture": (
            "I’m unable to provide details about internal architecture or file paths."
        ),
        "clone": (
            "I can’t help with building a clone of this system. "
            "Consider looking for general guidance on similar technologies."
        ),
        "detail_extraction": (
            "I’m not able to disclose internal details or exact file contents."
        ),
    }

    def __init__(self, fallback_handler: Optional[Callable[[str], str]] = None):
        """
        :param fallback_handler: Optional callable that receives the original query
                                 and returns a response for non‑protected queries.
                                 If omitted, a generic acknowledgement is used.
        """
        self.fallback_handler = fallback_handler or self._default_fallback

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def handle_query(self, query: str) -> str:
        """
        Analyse `query` and return an appropriate response.

        :param query: User supplied text.
        :return: Response string.
        """
        # Normalise whitespace for reliable matching
        normalized = " ".join(query.split())

        # Detection order matters – more specific checks first
        if self._matches_any(normalized, self._source_code_patterns):
            return self._responses["source_code"]
        if self._matches_any(normalized, self._architecture_patterns):
            return self._responses["architecture"]
        if self._matches_any(normalized, self._clone_patterns):
            return self._responses["clone"]
        if self._matches_any(normalized, self._detail_extraction_patterns):
            return self._responses["detail_extraction"]

        # No protected pattern matched – delegate to fallback
        return self.fallback_handler(normalized)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _matches_any(text: str, patterns: list[re.Pattern]) -> bool:
        """Return True if any pattern matches the text."""
        return any(p.search(text) for p in patterns)

    @staticmethod
    def _default_fallback(_query: str) -> str:
        """Simple generic response for non‑protected queries."""
        return "Your request has been received and will be processed."