import json
import os
from typing import Any, Dict, List, Set


class UserProxy:
    """
    Persistent representation of a user's intent, preferences, and communication style.
    The data is stored in a JSON file next to the module so that it survives across
    interpreter sessions.
    """

    _storage_file = os.path.join(os.path.dirname(__file__), "user_proxy_state.json")

    def __init__(self):
        # Load persisted state or initialise defaults
        self.preferences: Dict[str, Any] = {}
        self.style: Dict[str, Any] = {}
        self.anti_patterns: Set[str] = set()
        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state from JSON if it exists."""
        if os.path.isfile(self._storage_file):
            try:
                with open(self._storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.preferences = data.get("preferences", {})
                    self.style = data.get("style", {})
                    self.anti_patterns = set(data.get("anti_patterns", []))
            except Exception as e:
                # Corrupt file – start fresh but keep a backup
                backup = self._storage_file + ".bak"
                os.rename(self._storage_file, backup)
                print(f"[UserProxy] Failed to load state ({e}); backup created at {backup}")

    def _save_state(self) -> None:
        """Persist current state to JSON."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": list(self.anti_patterns),
        }
        with open(self._storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------------------- #
    # Preference accumulation
    # --------------------------------------------------------------------- #
    def update_preference(self, key: str, value: Any) -> None:
        """Add or update a user preference."""
        self.preferences[key] = value
        self._save_state()

    def update_style(self, key: str, value: Any) -> None:
        """Record a style hint (e.g., preferred tone, verbosity)."""
        self.style[key] = value
        self._save_state()

    def add_anti_pattern(self, pattern: str) -> None:
        """Register a pattern the user dislikes."""
        self.anti_patterns.add(pattern.lower())
        self._save_state()

    # --------------------------------------------------------------------- #
    # Decision helpers
    # --------------------------------------------------------------------- #
    def _matches_anti_patterns(self, text: str) -> bool:
        """Check if any anti‑pattern appears in the supplied text."""
        lowered = text.lower()
        return any(pat in lowered for pat in self.anti_patterns)

    def simulate_response(self, output: str) -> bool:
        """
        Simulate the user's approval of a given output.

        Returns:
            True  – user would approve
            False – user would reject
        """
        # Simple heuristic:
        # 1. Reject if any anti‑pattern is present.
        # 2. Prefer outputs that contain known style keywords.
        # 3. Otherwise fall back to a neutral approval.
        if self._matches_anti_patterns(output):
            return False

        # Check for style alignment (e.g., prefers concise, formal, etc.)
        # The style dict can hold boolean flags or keyword lists.
        # Example: {"tone": "formal", "keywords": ["please", "thank you"]}
        tone = self.style.get("tone")
        if tone:
            # Very naive check: look for the word that represents the tone
            if tone.lower() not in output.lower():
                # If a specific tone is required and not found, treat as mismatch
                return False

        keywords: List[str] = self.style.get("keywords", [])
        if keywords:
            if not any(kw.lower() in output.lower() for kw in keywords):
                # No preferred keyword found – treat as neutral (not a reject)
                pass

        # If we reach here, we assume approval
        return True

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    def clear_state(self) -> None:
        """Reset all stored information (useful for testing)."""
        self.preferences.clear()
        self.style.clear()
        self.anti_patterns.clear()
        if os.path.isfile(self._storage_file):
            os.remove(self._storage_file)


# Convenience singleton for the rest of the codebase
user_proxy = UserProxy()