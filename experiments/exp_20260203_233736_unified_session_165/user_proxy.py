"""
user_proxy.py

Implements a persistent representation of the user’s intent and personality.
The UserProxy accumulates preferences, style cues, and anti‑patterns across
interactions and can be consulted before finalising any output.

The class is deliberately lightweight – it stores its state in a JSON file
(`user_proxy_state.json`) located next to this module.  The state is loaded
on construction and saved automatically whenever it is mutated.

Typical usage:

    from user_proxy import UserProxy

    proxy = UserProxy()
    proxy.add_preference("prefers concise answers")
    proxy.add_style_pattern("uses bullet points")
    proxy.add_anti_pattern("dislikes excessive emojis")

    output = generate_some_text()
    if proxy.simulate_response(output):
        # proceed – user would approve
        ...
    else:
        # vetoed – adjust output or ask user
        ...

The `simulate_response` method implements a very simple heuristic:
* If any anti‑pattern string is found in the output → reject.
* If any style pattern is *required* but missing → reject.
* Otherwise → approve.

The method returns a tuple ``(approved: bool, reason: str)`` so callers can
log why a veto occurred.

"""

import json
import os
from pathlib import Path
from typing import List, Tuple


class UserProxy:
    """
    Persistent representation of a user’s preferences, communication style,
    and anti‑patterns.  The object can be queried to decide whether a given
    output aligns with the stored user model.
    """

    _STATE_FILE = Path(__file__).with_name("user_proxy_state.json")

    def __init__(self):
        # Load persisted state or initialise empty collections.
        self.preferences: List[str] = []
        self.style: List[str] = []          # Desired style cues (e.g., "bullet points")
        self.anti_patterns: List[str] = []  # Things the user dislikes

        self._load_state()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_state(self) -> None:
        """Load persisted state from JSON if the file exists."""
        if self._STATE_FILE.is_file():
            try:
                with open(self._STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.preferences = data.get("preferences", [])
                self.style = data.get("style", [])
                self.anti_patterns = data.get("anti_patterns", [])
            except (json.JSONDecodeError, OSError) as exc:
                # Corrupt file – start fresh but keep a backup for debugging.
                backup = self._STATE_FILE.with_suffix(".bak")
                self._STATE_FILE.rename(backup)
                print(f"[UserProxy] Warning: corrupted state file, backup created at {backup}.")
        else:
            # No file yet – nothing to load.
            pass

    def _save_state(self) -> None:
        """Serialise the current state to JSON."""
        data = {
            "preferences": self.preferences,
            "style": self.style,
            "anti_patterns": self.anti_patterns,
        }
        try:
            with open(self._STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            print(f"[UserProxy] Error saving state: {exc}")

    # --------------------------------------------------------------------- #
    # Mutators – automatically persist after modification
    # --------------------------------------------------------------------- #
    def add_preference(self, pref: str) -> None:
        """Add a new user preference if not already present."""
        pref = pref.strip()
        if pref and pref not in self.preferences:
            self.preferences.append(pref)
            self._save_state()

    def add_style_pattern(self, pattern: str) -> None:
        """Add a style cue the user prefers (e.g., 'bullet points')."""
        pattern = pattern.strip()
        if pattern and pattern not in self.style:
            self.style.append(pattern)
            self._save_state()

    def add_anti_pattern(self, anti: str) -> None:
        """Add something the user dislikes (e.g., 'excessive emojis')."""
        anti = anti.strip()
        if anti and anti not in self.anti_patterns:
            self.anti_patterns.append(anti)
            self._save_state()

    # --------------------------------------------------------------------- #
    # Core functionality
    # --------------------------------------------------------------------- #
    def simulate_response(self, output: str) -> Tuple[bool, str]:
        """
        Evaluate whether the supplied ``output`` would be approved by the user.

        Returns:
            (approved: bool, reason: str)

        The decision process is deliberately simple:
        1. If any anti‑pattern appears in the output → reject.
        2. If any style pattern is listed but not detected → reject.
        3. Otherwise → approve.

        This method can be extended with more sophisticated NLP checks
        without altering the public API.
        """
        lowered = output.lower()

        # 1. Check anti‑patterns
        for anti in self.anti_patterns:
            if anti.lower() in lowered:
                return False, f"Contains anti‑pattern '{anti}'."

        # 2. Enforce required style cues (if any are defined)
        missing_styles = [s for s in self.style if s.lower() not in lowered]
        if missing_styles:
            missing = ", ".join(missing_styles)
            return False, f"Missing required style cues: {missing}."

        # 3. All checks passed – user would approve
        return True, "Approved."

    # --------------------------------------------------------------------- #
    # Convenience
    # --------------------------------------------------------------------- #
    def clear_all(self) -> None:
        """Reset the stored model – useful for testing or user reset."""
        self.preferences.clear()
        self.style.clear()
        self.anti_patterns.clear()
        self._save_state()

    # --------------------------------------------------------------------- #
    # Human‑in‑the‑loop prompt (optional)
    # --------------------------------------------------------------------- #
    def ask_user_approval(self, output: str) -> bool:
        """
        Interactive helper that asks the developer (or a real user) whether the
        output aligns with the stored model.  Returns True if the user confirms
        approval; otherwise False.
        """
        approved, reason = self.simulate_response(output)
        if approved:
            return True

        # If we are running in an environment where stdin is available, prompt.
        try:
            print(f"[UserProxy] Auto‑veto reason: {reason}")
            resp = input("Would the user still approve this output? (y/n): ").strip().lower()
            return resp.startswith("y")
        except Exception:
            # Non‑interactive environment – default to the simulated decision.
            return approved


# -------------------------------------------------------------------------
# Module‑level singleton for convenience (optional)
# -------------------------------------------------------------------------
_user_proxy_instance = None


def get_user_proxy() -> UserProxy:
    """Return a shared UserProxy instance for the current process."""
    global _user_proxy_instance
    if _user_proxy_instance is None:
        _user_proxy_instance = UserProxy()
    return _user_proxy_instance


if __name__ == "__main__":
    # Simple sanity test when run directly.
    proxy = get_user_proxy()
    proxy.add_anti_pattern("excessive emojis")
    proxy.add_style_pattern("bullet points")
    test_output = "Here are the results:\n- Item A\n- Item B"
    ok, msg = proxy.simulate_response(test_output)
    print(f"Approval: {ok}, Reason: {msg}")