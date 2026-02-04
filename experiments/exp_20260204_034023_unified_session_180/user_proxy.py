"""User Proxy Module

Provides a persistent representation of a user's intent, preferences,
communication style, and anti‑patterns. The proxy can be consulted
before finalising any output to ensure it aligns with the user's
expectations.

The implementation is deliberately lightweight: data is stored in a
JSON file (`user_proxy_state.json`) alongside this module.  The class
offers simple methods for updating the stored state and for simulating
a user approval decision based on the accumulated knowledge.
"""

import json
import os
from typing import Any, Dict, List


class UserProxy:
    """Persistent representation of a user's preferences, style and dislikes.

    Attributes
    ----------
    preferences: Dict[str, Any]
        Arbitrary key‑value pairs representing the user's stated preferences.
    style: List[str]
        Tokens or patterns that capture the user's preferred communication style.
    anti_patterns: List[str]
        Sub‑strings or patterns that the user explicitly dislikes; presence in
        an output triggers a rejection.
    _state_file: str
        Path to the JSON file used for persistence.
    """

    def __init__(self, state_dir: str = None):
        """Initialise the proxy, loading persisted state if available.

        Parameters
        ----------
        state_dir: str, optional
            Directory where the state file should live.  If omitted the
            directory of this module is used.
        """
        self._state_file = os.path.join(
            state_dir or os.path.dirname(__file__), "user_proxy_state.json"
        )
        self.preferences: Dict[str, Any] = {}
        self.style: List[str] = []
        self.anti_patterns: List[str] = []

        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted data from the JSON state file."""
        if not os.path.isfile(self._state_file):
            # No persisted state yet – start with empty structures.
            return
        try:
            with open(self._state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.preferences = data.get("preferences", {})
                self.style = data.get("style", [])
                self.anti_patterns = data.get("anti_patterns", [])
        except (json.JSONDecodeError, OSError) as exc:
            # Corrupt or unreadable state – start fresh but keep the file for debugging.
            print(f"[UserProxy] Warning: could not read state file: {exc}")

    def _save_state(self) -> None:
        """Serialise current data to the JSON state file."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        try:
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            print(f"[UserProxy] Error: could not write state file: {exc}")

    # --------------------------------------------------------------------- #
    # Public mutation API
    # --------------------------------------------------------------------- #
    def add_preference(self, key: str, value: Any) -> None:
        """Record or update a user preference."""
        self.preferences[key] = value
        self._save_state()

    def add_style_pattern(self, pattern: str) -> None:
        """Add a communication style token/pattern."""
        if pattern not in self.style:
            self.style.append(pattern)
            self._save_state()

    def add_anti_pattern(self, pattern: str) -> None:
        """Add a pattern the user dislikes."""
        if pattern not in self.anti_patterns:
            self.anti_patterns.append(pattern)
            self._save_state()

    # --------------------------------------------------------------------- #
    # Decision logic
    # --------------------------------------------------------------------- #
    def simulate_response(self, output: str) -> bool:
        """Ask “Would the user approve this?” based on stored knowledge.

        The method performs a simple heuristic check:
        * If any anti‑pattern appears in the output → reject.
        * If style patterns are defined, at least one should appear → approve,
          otherwise treat as a neutral approval (True) to avoid false negatives.

        Returns
        -------
        bool
            ``True`` if the simulated user would approve, ``False`` otherwise.
        """
        lowered = output.lower()

        # Reject if any anti‑pattern is found.
        for anti in self.anti_patterns:
            if anti.lower() in lowered:
                return False

        # If style patterns exist, encourage their presence.
        if self.style:
            for pat in self.style:
                if pat.lower() in lowered:
                    return True
            # No style pattern matched – still not a hard reject, but we can
            # consider it a neutral approval.  Returning True keeps the workflow
            # moving; callers can decide to surface a warning if desired.
            return True

        # No style constraints → approve by default.
        return True

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:
        return (
            f"UserProxy(preferences={self.preferences}, "
            f"style={self.style}, anti_patterns={self.anti_patterns})"
        )