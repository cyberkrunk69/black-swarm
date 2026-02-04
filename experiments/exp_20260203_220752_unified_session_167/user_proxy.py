"""
User Proxy Module
-----------------

Provides a persistent representation of the user's intent, preferences,
communication style, and known anti‑patterns. The proxy can be queried
to simulate whether a generated output would be approved by the user.

This module is deliberately lightweight and does not depend on any
external services so it can be imported safely from any part of the
code base.

Typical usage:

    from user_proxy import UserProxy

    proxy = UserProxy()
    proxy.update_preferences({"theme": "dark", "language": "en"})
    proxy.add_anti_pattern("excessive_jargon")
    if proxy.simulate_response(generated_text):
        # proceed with finalisation
        ...
    else:
        # request a rewrite or further refinement
        ...

The proxy persists its state to a JSON file in the same directory so
that preferences accumulate across multiple runs.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class UserProxy:
    """
    Persistent representation of a user's intent, style, and dislikes.

    Attributes
    ----------
    preferences : Dict[str, Any]
        Accumulated key/value pairs describing user preferences.
    style : Dict[str, Any]
        High‑level description of the user's communication patterns
        (e.g., tone, formality, verbosity).
    anti_patterns : List[str]
        List of identifiers for patterns the user explicitly dislikes.
    _storage_path : Path
        Location of the JSON file used for persistence.
    """

    _DEFAULT_STORAGE = "user_proxy_state.json"

    def __init__(self, storage_path: str | os.PathLike | None = None) -> None:
        """
        Initialise the proxy, loading persisted state if it exists.

        Parameters
        ----------
        storage_path : optional
            Custom location for the JSON persistence file.  If omitted,
            a file named ``user_proxy_state.json`` in the same directory
            as this module is used.
        """
        self._storage_path = Path(storage_path) if storage_path else Path(__file__).parent / self._DEFAULT_STORAGE

        # Initialise empty structures; they will be overwritten if a state file exists.
        self.preferences: Dict[str, Any] = {}
        self.style: Dict[str, Any] = {}
        self.anti_patterns: List[str] = []

        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state from the JSON file if present."""
        if self._storage_path.is_file():
            try:
                with self._storage_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                self.preferences = data.get("preferences", {})
                self.style = data.get("style", {})
                self.anti_patterns = data.get("anti_patterns", [])
            except (json.JSONDecodeError, OSError) as exc:
                # Corrupted file – start fresh but keep a trace for debugging.
                print(f"[UserProxy] Warning: could not load state ({exc}); starting with empty state.")
                self.preferences = {}
                self.style = {}
                self.anti_patterns = []
        else:
            # No persisted file – nothing to load.
            pass

    def _save_state(self) -> None:
        """Persist the current state to disk."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        try:
            with self._storage_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            print(f"[UserProxy] Error: could not persist state ({exc}).")

    # --------------------------------------------------------------------- #
    # Public mutation APIs
    # --------------------------------------------------------------------- #
    def update_preferences(self, new_prefs: Dict[str, Any]) -> None:
        """
        Merge new preference entries into the existing dictionary.

        Parameters
        ----------
        new_prefs : dict
            Preference keys and values to add or overwrite.
        """
        self.preferences.update(new_prefs)
        self._save_state()

    def update_style(self, new_style: Dict[str, Any]) -> None:
        """
        Merge new style descriptors into the existing style dictionary.

        Parameters
        ----------
        new_style : dict
            Style keys (e.g., "tone", "verbosity") and their desired values.
        """
        self.style.update(new_style)
        self._save_state()

    def add_anti_pattern(self, pattern_id: str) -> None:
        """
        Register a pattern that the user explicitly dislikes.

        Parameters
        ----------
        pattern_id : str
            Identifier for the anti‑pattern (e.g., "overuse_of_acronyms").
        """
        if pattern_id not in self.anti_patterns:
            self.anti_patterns.append(pattern_id)
            self._save_state()

    # --------------------------------------------------------------------- #
    # Decision logic
    # --------------------------------------------------------------------- #
    def simulate_response(self, output: str) -> bool:
        """
        Simulate whether the user would approve a given output.

        The algorithm is intentionally simple but extensible:
          * If any known anti‑pattern token appears in the output, reject.
          * If the output deviates strongly from the recorded style (e.g.,
            excessive length when the user prefers concise answers), reject.
          * Otherwise, approve.

        Parameters
        ----------
        output : str
            The generated text to evaluate.

        Returns
        -------
        bool
            ``True`` if the user would likely approve, ``False`` otherwise.
        """
        # 1. Anti‑pattern check – a very naive substring search.
        lowered = output.lower()
        for anti in self.anti_patterns:
            if anti.lower() in lowered:
                # Immediate veto
                return False

        # 2. Style heuristics – currently supports only a few basic cues.
        #    Extend this block as more style attributes are captured.
        if self.style:
            # Example: preferred tone ("formal", "casual")
            preferred_tone = self.style.get("tone")
            if preferred_tone:
                # Very simple heuristic: look for hallmark words.
                formal_markers = {"therefore", "hence", "moreover", "thus"}
                casual_markers = {"yeah", "cool", "awesome", "gotcha"}

                if preferred_tone == "formal" and any(word in lowered for word in casual_markers):
                    return False
                if preferred_tone == "casual" and any(word in lowered for word in formal_markers):
                    return False

            # Example: verbosity preference (max words)
            max_words = self.style.get("max_words")
            if isinstance(max_words, int):
                word_count = len(output.split())
                if word_count > max_words:
                    return False

        # If none of the veto conditions triggered, approve.
        return True

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    def __repr__(self) -> str:
        return (
            f"UserProxy(preferences={self.preferences}, "
            f"style={self.style}, anti_patterns={self.anti_patterns})"
        )


# -------------------------------------------------------------------------
# Convenience singleton for quick imports throughout the code base.
# -------------------------------------------------------------------------
# The first import creates the persisted instance; subsequent imports
# reuse the same object (module globals are singletons per interpreter).
user_proxy = UserProxy()