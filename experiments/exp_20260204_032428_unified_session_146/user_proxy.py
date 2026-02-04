import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class UserProxy:
    """
    Persistent representation of a user's intent, personality and preferences.

    The class stores:
        - preferences: key/value pairs accumulated from past interactions.
        - style: observed communication patterns (e.g., tone, verbosity).
        - anti_patterns: list of patterns the user dislikes.

    The data is persisted to a JSON file (``user_proxy_state.json``) inside the
    experiment directory, allowing the proxy to survive across multiple runs.
    """

    _STATE_FILE = Path(__file__).with_name("user_proxy_state.json")

    def __init__(self):
        self.preferences: Dict[str, Any] = {}
        self.style: Dict[str, Any] = {}
        self.anti_patterns: List[str] = []
        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state if the JSON file exists."""
        if self._STATE_FILE.is_file():
            try:
                with open(self._STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.preferences = data.get("preferences", {})
                self.style = data.get("style", {})
                self.anti_patterns = data.get("anti_patterns", [])
            except (json.JSONDecodeError, OSError) as e:
                # Corrupt file – start fresh but keep a backup for debugging.
                backup = self._STATE_FILE.with_suffix(".bak")
                self._STATE_FILE.rename(backup)
                self.preferences = {}
                self.style = {}
                self.anti_patterns = []

    def _save_state(self) -> None:
        """Write the current state to the JSON file."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        tmp_path = self._STATE_FILE.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(self._STATE_FILE)

    # --------------------------------------------------------------------- #
    # Public API – updating the model
    # --------------------------------------------------------------------- #
    def update_preference(self, key: str, value: Any) -> None:
        """Add or update a single preference."""
        self.preferences[key] = value
        self._save_state()

    def update_style(self, attribute: str, value: Any) -> None:
        """Record a style attribute (e.g., "tone": "formal")."""
        self.style[attribute] = value
        self._save_state()

    def add_anti_pattern(self, pattern: str) -> None:
        """Register a pattern the user dislikes."""
        if pattern not in self.anti_patterns:
            self.anti_patterns.append(pattern)
            self._save_state()

    # --------------------------------------------------------------------- #
    # Decision logic
    # --------------------------------------------------------------------- #
    def _matches_style(self, output: str) -> bool:
        """
        Very lightweight heuristic to see if the output respects the stored style.
        For now we only check for simple anti‑patterns and a basic tone match.
        """
        lowered = output.lower()
        # Reject if any anti‑pattern appears verbatim.
        for pat in self.anti_patterns:
            if pat.lower() in lowered:
                return False

        # Example tone check: if user prefers formal tone, discourage excessive slang.
        preferred_tone = self.style.get("tone")
        if preferred_tone == "formal":
            slang_markers = [" lol ", " omg ", " btw ", " gotta ", " kinda "]
            if any(marker in lowered for marker in slang_markers):
                return False
        return True

    def simulate_response(self, output: str) -> bool:
        """
        Simulate the user's approval of a given output.

        Returns:
            True  – the user would approve the output.
            False – the user would reject it.
        """
        # Simple rule‑based approach: check style compliance and known preferences.
        if not self._matches_style(output):
            return False

        # Preference‑based veto: if the output mentions something the user explicitly
        # dislikes (e.g., a banned topic), reject.
        banned_topics = self.preferences.get("banned_topics", [])
        lowered = output.lower()
        for topic in banned_topics:
            if topic.lower() in lowered:
                return False

        # If we reach here, assume approval.
        return True

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    def dump_state(self) -> Dict[str, Any]:
        """Return a copy of the internal state (useful for debugging)."""
        return {
            "preferences": dict(self.preferences),
            "style": dict(self.style),
            "anti_patterns": list(self.anti_patterns),
        }

    # --------------------------------------------------------------------- #
    # Integration hook
    # --------------------------------------------------------------------- #
    def ask_user_approval(self, output: str) -> bool:
        """
        Interactive helper used by the execution framework.
        It asks the question “Would the user approve this?” and returns the answer.
        In a non‑interactive environment this simply delegates to ``simulate_response``.
        """
        # In production this could be replaced by a real user prompt.
        return self.simulate_response(output)


# If this module is run directly, provide a tiny demo.
if __name__ == "__main__":
    proxy = UserProxy()
    proxy.update_style("tone", "formal")
    proxy.add_anti_pattern("shouty")
    proxy.update_preference("banned_topics", ["politics", "spam"])

    test_output = "Here's a concise, formal summary of the report."
    print("User would approve:", proxy.ask_user_approval(test_output))