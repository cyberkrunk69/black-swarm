"""
user_proxy.py

Persistent representation of the user (CEO) for internal reasoning.

The UserProxy accumulates preferences, communication style cues, and
anti‑patterns (things the user explicitly dislikes).  It can be queried
to decide whether a generated output aligns with the user's established
persona.

This module is deliberately lightweight – it stores data in‑memory and
offers simple JSON‑serialisation hooks for persistence if the surrounding
system wishes to checkpoint it between sessions.
"""

import json
from typing import Any, Dict, List, Optional


class UserProxy:
    """
    Core data‑structure that models the user's intent, personality and
    tolerances.  All fields are mutable so the system can enrich the model
    as interactions progress.
    """

    def __init__(
        self,
        preferences: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        anti_patterns: Optional[List[str]] = None,
    ) -> None:
        """
        Initialise a new UserProxy.

        Args:
            preferences: High‑level preferences (e.g. {"tone": "formal"}).
            style: Communication‑style cues (e.g. {"sentence_length": "short"}).
            anti_patterns: List of strings the user explicitly dislikes.
        """
        self.preferences: Dict[str, Any] = preferences or {}
        self.style: Dict[str, Any] = style or {}
        self.anti_patterns: List[str] = anti_patterns or []

    # --------------------------------------------------------------------- #
    # Mutators – called by other parts of the system to enrich the model.
    # --------------------------------------------------------------------- #
    def update_preference(self, key: str, value: Any) -> None:
        """Add or update a single preference."""
        self.preferences[key] = value

    def update_style(self, key: str, value: Any) -> None:
        """Add or update a single style cue."""
        self.style[key] = value

    def add_anti_pattern(self, pattern: str) -> None:
        """Record a pattern the user hates (exact match or regex)."""
        if pattern not in self.anti_patterns:
            self.anti_patterns.append(pattern)

    # --------------------------------------------------------------------- #
    # Persistence helpers – optional, used by the surrounding framework.
    # --------------------------------------------------------------------- #
    def to_dict(self) -> Dict[str, Any]:
        """Serialise the proxy to a plain dict."""
        return {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProxy":
        """Re‑hydrate a UserProxy from a dict."""
        return cls(
            preferences=data.get("preferences"),
            style=data.get("style"),
            anti_patterns=data.get("anti_patterns"),
        )

    def dump_to_json(self, path: str) -> None:
        """Write the current state to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_json(cls, path: str) -> "UserProxy":
        """Load a UserProxy from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # --------------------------------------------------------------------- #
    # Core logic – decide if a generated output aligns with the user model.
    # --------------------------------------------------------------------- #
    def _matches_preferences(self, output: str) -> bool:
        """
        Very lightweight heuristic: checks for presence of preference keywords.
        Real implementations could use NLP models; here we keep it simple.
        """
        for key, val in self.preferences.items():
            # Example: if preference is {"tone": "formal"}, we look for
            # a cue word that signals formality.
            # This placeholder simply ensures the value string appears.
            if isinstance(val, str) and val.lower() not in output.lower():
                return False
        return True

    def _matches_style(self, output: str) -> bool:
        """
        Checks style cues.  For demonstration we support a few basic cues.
        """
        # Example cue: "sentence_length": "short"
        sentence_len = self.style.get("sentence_length")
        if sentence_len == "short":
            # Rough heuristic: average sentence length < 12 words
            sentences = [s.strip() for s in output.split('.') if s]
            avg_len = (
                sum(len(s.split()) for s in sentences) / len(sentences)
                if sentences
                else 0
            )
            if avg_len > 12:
                return False
        elif sentence_len == "long":
            sentences = [s.strip() for s in output.split('.') if s]
            avg_len = (
                sum(len(s.split()) for s in sentences) / len(sentences)
                if sentences
                else 0
            )
            if avg_len < 20:
                return False
        # Additional style checks can be added here.
        return True

    def _contains_anti_patterns(self, output: str) -> bool:
        """
        Returns True if any anti‑pattern is detected in the output.
        Simple substring check; can be upgraded to regex matching.
        """
        lowered = output.lower()
        for pat in self.anti_patterns:
            if pat.lower() in lowered:
                return True
        return False

    def simulate_response(self, output: str) -> bool:
        """
        Main entry point: evaluate the generated output against the stored
        user model.

        Returns:
            True  – user would approve the output.
            False – user would reject it (veto).
        """
        # Quick veto on any anti‑pattern.
        if self._contains_anti_patterns(output):
            return False

        # Preference and style checks – both must pass.
        if not self._matches_preferences(output):
            return False
        if not self._matches_style(output):
            return False

        # If all checks pass, we assume approval.
        return True

    # --------------------------------------------------------------------- #
    # Interactive helper – used by the system before finalising a task.
    # --------------------------------------------------------------------- #
    def ask_user_approval(self, output: str) -> bool:
        """
        Placeholder for a real UI prompt.  In the current environment we
        simply call `simulate_response`.  The surrounding framework may
        replace this with an actual dialog with the CEO.
        """
        return self.simulate_response(output)


# ------------------------------------------------------------------------- #
# Example usage (not executed on import, kept for reference)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    proxy = UserProxy()
    proxy.update_preference("tone", "formal")
    proxy.update_style("sentence_length", "short")
    proxy.add_anti_pattern("jargon")
    sample = "This is a concise, formal summary."
    print("Approval:", proxy.ask_user_approval(sample))