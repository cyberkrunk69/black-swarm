"""
user_proxy.py

Persistent representation of a user's intent, preferences, and communication style.
Used by the CEO/CEO node to align generated outputs with the user's expectations.

The UserProxy class:
- Accumulates preferences and style cues over time.
- Stores anti‑patterns (phrases or concepts the user dislikes).
- Persists its state to a JSON file so that knowledge survives across sessions.
- Provides `simulate_response` to approve or reject a candidate output.
- Offers a simple `ask_user_approval` hook that can be overridden for real‑world
  interaction (e.g., prompting the user or an external system).
"""

import json
import os
import re
from typing import Any, Dict, List, Optional


class UserProxy:
    """
    Persistent user model.

    Attributes
    ----------
    preferences : Dict[str, Any]
        Accumulated preferences keyed by topic or keyword.
    style : Dict[str, Any]
        Preferred communication style (e.g., tone, verbosity).
    anti_patterns : List[str]
        List of substrings/regexes the user finds objectionable.
    _state_path : str
        Path to the JSON file used for persistence.
    """

    _DEFAULT_STATE_FILE = "user_proxy_state.json"

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialise the proxy, loading persisted state if available.

        Parameters
        ----------
        storage_dir : Optional[str]
            Directory where the state file lives. If ``None`` the directory of this
            file is used.
        """
        if storage_dir is None:
            storage_dir = os.path.dirname(__file__)
        self._state_path = os.path.join(storage_dir, self._DEFAULT_STATE_FILE)

        # Initialise empty structures; they will be overwritten by _load_state if possible.
        self.preferences: Dict[str, Any] = {}
        self.style: Dict[str, Any] = {}
        self.anti_patterns: List[str] = []

        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state from ``self._state_path`` if the file exists."""
        if os.path.isfile(self._state_path):
            try:
                with open(self._state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.preferences = data.get("preferences", {})
                self.style = data.get("style", {})
                self.anti_patterns = data.get("anti_patterns", [])
            except (json.JSONDecodeError, OSError) as exc:
                # Corrupt or unreadable file – start fresh but keep a warning.
                print(f"[UserProxy] Warning: could not load state ({exc}); starting empty.")
                self.preferences = {}
                self.style = {}
                self.anti_patterns = []

    def _save_state(self) -> None:
        """Persist current state to ``self._state_path``."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        try:
            with open(self._state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            print(f"[UserProxy] Error: could not save state ({exc}).")

    # --------------------------------------------------------------------- #
    # Interaction API
    # --------------------------------------------------------------------- #
    def update_from_interaction(self, interaction: Dict[str, Any]) -> None:
        """
        Incorporate new information gleaned from a user interaction.

        The ``interaction`` dict can contain any of the following keys:
          - ``preferences`` : Dict[str, Any]
          - ``style``       : Dict[str, Any]
          - ``anti_patterns`` : List[str]

        The method merges the supplied data with the existing state.
        """
        if not isinstance(interaction, dict):
            raise ValueError("interaction must be a dictionary")

        # Merge preferences
        pref = interaction.get("preferences", {})
        if isinstance(pref, dict):
            self.preferences.update(pref)

        # Merge style cues
        style = interaction.get("style", {})
        if isinstance(style, dict):
            self.style.update(style)

        # Extend anti‑patterns
        anti = interaction.get("anti_patterns", [])
        if isinstance(anti, list):
            # Avoid duplicates while preserving order
            for pattern in anti:
                if pattern not in self.anti_patterns:
                    self.anti_patterns.append(pattern)

        self._save_state()

    # --------------------------------------------------------------------- #
    # Decision logic
    # --------------------------------------------------------------------- #
    def _contains_anti_pattern(self, text: str) -> bool:
        """
        Check whether ``text`` matches any anti‑pattern.

        Patterns are interpreted as regular expressions; a simple substring
        match is also supported.
        """
        lowered = text.lower()
        for pat in self.anti_patterns:
            try:
                if re.search(pat, lowered):
                    return True
            except re.error:
                # If the pattern is not a valid regex, fall back to substring search.
                if pat.lower() in lowered:
                    return True
        return False

    def _matches_style(self, text: str) -> bool:
        """
        Very lightweight style compliance check.

        Currently supports:
          - ``tone`` : "formal" | "informal"
          - ``verbosity`` : "concise" | "verbose"

        Returns ``True`` if the output respects the stored style, ``False`` otherwise.
        """
        if not self.style:
            return True  # No style constraints defined.

        # Tone check – naive keyword approach.
        tone = self.style.get("tone")
        if tone == "formal":
            # Formal tone tends to avoid contractions and slang.
            if re.search(r"\b(can't|won't|n't|gonna|wanna|y'all|lol)\b", text.lower()):
                return False
        elif tone == "informal":
            # Informal tone may include contractions; we accept anything.
            pass

        # Verbosity check.
        verbosity = self.style.get("verbosity")
        if verbosity == "concise":
            # Roughly, concise means <= 20 words per sentence on average.
            sentences = re.split(r"[.!?]\s*", text.strip())
            if sentences:
                avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
                if avg_len > 20:
                    return False
        elif verbosity == "verbose":
            # Expect at least 15 words per sentence.
            sentences = re.split(r"[.!?]\s*", text.strip())
            if sentences:
                avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
                if avg_len < 15:
                    return False

        return True

    def simulate_response(self, candidate_output: str) -> bool:
        """
        Decide whether the user would approve ``candidate_output``.

        The decision process:
          1. Reject immediately if any anti‑pattern is present.
          2. Reject if the output violates known style constraints.
          3. If preferences contain keyword hints, give a small boost;
             otherwise, default to approval.

        Returns
        -------
        bool
            ``True`` if the user would likely approve, ``False`` otherwise.
        """
        if self._contains_anti_pattern(candidate_output):
            return False

        if not self._matches_style(candidate_output):
            return False

        # Simple preference boost: if any preference keyword appears, we treat it as positive.
        # This is intentionally lightweight; more sophisticated scoring can be added later.
        if self.preferences:
            lowered = candidate_output.lower()
            for keyword in self.preferences.keys():
                if keyword.lower() in lowered:
                    return True  # Preference match => approve

        # Default to approval when no disqualifying factors are found.
        return True

    # --------------------------------------------------------------------- #
    # Hook for interactive approval (can be overridden)
    # --------------------------------------------------------------------- #
    def ask_user_approval(self, candidate_output: str) -> bool:
        """
        Prompt the real user for approval.

        In the default implementation we rely on ``simulate_response``.
        Override this method in a subclass or monkey‑patch it to integrate
        with an actual UI / messaging system.
        """
        return self.simulate_response(candidate_output)

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:
        return (
            f"UserProxy(preferences={list(self.preferences.keys())}, "
            f"style={self.style}, anti_patterns={self.anti_patterns})"
        )