import json
import os
from typing import Any, Dict, List, Optional


class UserProxy:
    """
    Persistent representation of a user's intent, preferences and style.
    The data is stored in a JSON file (`user_proxy_state.json`) inside the same
    experiment directory so that it survives across multiple runs.
    """

    _STATE_FILE = "user_proxy_state.json"

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialise the proxy.

        Args:
            base_path: Directory where the state file lives.
                       If None, uses the directory of this file.
        """
        self.base_path = base_path or os.path.dirname(__file__)
        self.state_path = os.path.join(self.base_path, self._STATE_FILE)

        # Default structure
        self.preferences: Dict[str, Any] = {}
        self.style: Dict[str, Any] = {
            "tone": "neutral",          # e.g. formal, casual, witty
            "verbosity": "medium",      # low, medium, high
            "formatting": "plain"       # plain, markdown, html
        }
        self.anti_patterns: List[str] = []   # things the user dislikes

        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state if it exists."""
        if os.path.isfile(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.preferences = data.get("preferences", {})
                self.style = data.get("style", self.style)
                self.anti_patterns = data.get("anti_patterns", [])
            except Exception as e:
                # Corrupt file – start fresh but keep a backup
                backup_path = self.state_path + ".bak"
                os.rename(self.state_path, backup_path)
                print(f"[UserProxy] Corrupt state file; moved to {backup_path}. Error: {e}")

    def _save_state(self) -> None:
        """Persist current state to disk."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # --------------------------------------------------------------------- #
    # Public API – updating knowledge
    # --------------------------------------------------------------------- #
    def update_preference(self, key: str, value: Any) -> None:
        """Add or update a single preference."""
        self.preferences[key] = value
        self._save_state()

    def update_style(self, key: str, value: Any) -> None:
        """Change a style attribute (tone, verbosity, formatting, …)."""
        self.style[key] = value
        self._save_state()

    def add_anti_pattern(self, pattern: str) -> None:
        """Record a pattern the user dislikes."""
        if pattern not in self.anti_patterns:
            self.anti_patterns.append(pattern)
            self._save_state()

    # --------------------------------------------------------------------- #
    # Decision helpers
    # --------------------------------------------------------------------- #
    def _contains_anti_pattern(self, text: str) -> bool:
        """Simple substring check for anti‑patterns."""
        lowered = text.lower()
        return any(pat.lower() in lowered for pat in self.anti_patterns)

    def simulate_response(self, output: str) -> bool:
        """
        Simulate the user's approval of a generated output.

        Returns:
            True  – user would approve
            False – user would veto
        """
        # 1. Reject if any anti‑pattern is present
        if self._contains_anti_pattern(output):
            return False

        # 2. Basic style checks – can be expanded later
        #    * Tone match (very naive: look for keywords)
        tone = self.style.get("tone", "neutral")
        if tone == "formal" and any(word in output.lower() for word in ["hey", "yo", "thanks!"]):
            return False
        if tone == "casual" and any(word in output.lower() for word in ["respectfully", "sincerely"]):
            return False

        # 3. Verbosity – crude length check
        verbosity = self.style.get("verbosity", "medium")
        length = len(output.split())
        if verbosity == "low" and length > 50:
            return False
        if verbosity == "high" and length < 20:
            return False

        # If none of the veto rules triggered, assume approval
        return True

    # --------------------------------------------------------------------- #
    # Convenience
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:
        return (
            f"UserProxy(preferences={self.preferences}, "
            f"style={self.style}, anti_patterns={self.anti_patterns})"
        )