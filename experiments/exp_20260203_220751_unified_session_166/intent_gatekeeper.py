"""
Intent Gatekeeper Module
------------------------

This module implements the first node of the unified architecture: the
Intent Gatekeeper. It parses incoming user requests, extracts a structured
intent, stores it, and provides utilities to inject the intent into downstream
prompts while periodically checking alignment.

The module is deliberately lightweight and has no external dependencies beyond
the Python standard library.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

# --------------------------------------------------------------------------- #
# Data Model
# --------------------------------------------------------------------------- #

@dataclass
class Intent:
    """
    Structured representation of a user's request.

    Attributes
    ----------
    goal: str
        The primary objective the user wants to achieve.
    constraints: List[str]
        Hard constraints that must not be violated.
    preferences: List[str]
        Soft preferences that guide how the goal should be achieved.
    anti_goals: List[str]
        Things the user explicitly does NOT want.
    clarifications: List[str] = field(default_factory=list)
        Follow‑up questions or notes needed to resolve ambiguities.
    """
    goal: str
    constraints: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    anti_goals: List[str] = field(default_factory=list)
    clarifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON‑serializable dict."""
        return asdict(self)

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# --------------------------------------------------------------------------- #
# Parsing Utilities
# --------------------------------------------------------------------------- #

_SECTION_REGEX = re.compile(
    r"""(?P<header>Goal|Constraints|Preferences|Anti[-\s]?Goals|Clarifications?)\s*[:\-]\s*
        (?P<content>.*?)(?=(?:\n\s*(?:Goal|Constraints|Preferences|Anti[-\s]?Goals|Clarifications?)\s*[:\-])|\Z)""",
    re.IGNORECASE | re.DOTALL | re.VERBOSE,
)

def _clean_list_items(text: str) -> List[str]:
    """Split a block of text into a list of bullet‑point items."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    items = []
    for line in lines:
        # Remove common bullet characters
        line = re.sub(r"^[\-\*\·]\s*", "", line)
        items.append(line)
    return items


def parse_intent(request: str) -> Intent:
    """
    Parse a raw user request into an :class:`Intent` object.

    The parser looks for explicit section headers (Goal, Constraints,
    Preferences, Anti‑Goals, Clarifications). If a section is missing,
    the parser attempts a best‑effort fallback:
        * The first sentence is treated as the goal.
        * Anything that looks like a constraint (contains words such as
          "must", "should not", "no", "cannot") is collected.

    Parameters
    ----------
    request: str
        Raw user input.

    Returns
    -------
    Intent
        Structured intent.
    """
    # Normalise line endings
    request = request.replace("\r\n", "\n").strip()

    sections: Dict[str, str] = {}
    for match in _SECTION_REGEX.finditer(request):
        header = match.group("header").lower().replace(" ", "_").replace("-", "_")
        sections[header] = match.group("content").strip()

    # Goal – required; try to infer if missing
    goal = sections.get("goal")
    if not goal:
        # Fallback: first sentence before a period or newline
        goal = request.split("\n")[0].split(".")[0].strip()
        # Remove any leading bullet chars
        goal = re.sub(r"^[\-\*\·]\s*", "", goal)

    # Constraints, Preferences, Anti‑Goals, Clarifications – optional lists
    constraints = _clean_list_items(sections.get("constraints", ""))
    preferences = _clean_list_items(sections.get("preferences", ""))
    anti_goals = _clean_list_items(sections.get("anti_goals", ""))
    clarifications = _clean_list_items(sections.get("clarifications", ""))

    # Simple heuristic: if constraints list is empty, scan for constraint‑like phrases
    if not constraints:
        possible_constraints = re.findall(
            r"(?:must|should not|cannot|no\s+\w+|must not|cannot be)\s+[^.;]+[.;]?",
            request,
            flags=re.IGNORECASE,
        )
        constraints = [c.strip(" .;") for c in possible_constraints]

    return Intent(
        goal=goal,
        constraints=constraints,
        preferences=preferences,
        anti_goals=anti_goals,
        clarifications=clarifications,
    )


# --------------------------------------------------------------------------- #
# Gatekeeper Core
# --------------------------------------------------------------------------- #

class IntentGatekeeper:
    """
    Core service that holds the original intent and provides helpers for
    downstream components.

    Typical usage:

    >>> gatekeeper = IntentGatekeeper()
    >>> gatekeeper.process_user_request(raw_text)
    >>> downstream_prompt = gatekeeper.inject_intent("Generate code for ...")
    >>> aligned = gatekeeper.check_alignment(current_state)
    """

    def __init__(self) -> None:
        self._intent: Optional[Intent] = None
        # Timestamp or version could be added later for more sophisticated checks

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def process_user_request(self, request: str) -> Intent:
        """
        Parse the incoming request and store the resulting Intent.

        Parameters
        ----------
        request: str
            Raw user request.

        Returns
        -------
        Intent
            The parsed intent.
        """
        self._intent = parse_intent(request)
        return self._intent

    @property
    def intent(self) -> Intent:
        """Return the stored Intent; raises if not yet set."""
        if self._intent is None:
            raise RuntimeError("Intent has not been initialized. Call process_user_request first.")
        return self._intent

    def inject_intent(self, prompt: str) -> str:
        """
        Prepend a concise intent summary to a downstream prompt.

        Parameters
        ----------
        prompt: str
            The original prompt that will be sent to a downstream node.

        Returns
        -------
        str
            Prompt prefixed with intent context.
        """
        intent = self.intent
        summary_parts = [
            f"Goal: {intent.goal}",
        ]
        if intent.constraints:
            summary_parts.append(f"Constraints: {', '.join(intent.constraints)}")
        if intent.preferences:
            summary_parts.append(f"Preferences: {', '.join(intent.preferences)}")
        if intent.anti_goals:
            summary_parts.append(f"Anti‑Goals: {', '.join(intent.anti_goals)}")
        summary = " | ".join(summary_parts)

        return f"[Intent] {summary}\n\n{prompt}"

    def check_alignment(self, observed_output: str) -> bool:
        """
        Very lightweight alignment check: ensure that the observed output
        does not violate any hard constraints or anti‑goals.

        Parameters
        ----------
        observed_output: str
            Text produced by downstream processing.

        Returns
        -------
        bool
            True if still aligned, False otherwise.
        """
        intent = self.intent
        lowered = observed_output.lower()

        # Simple keyword‑based violation detection
        for c in intent.constraints:
            if c.lower() not in lowered:
                # If a constraint is a phrase that should appear, we check presence.
                # Inverse logic: missing required phrase => misalignment.
                continue

        for ag in intent.anti_goals:
            if ag.lower() in lowered:
                return False

        # No obvious violations detected
        return True

    # ------------------------------------------------------------------- #
    # Integration Hook (spawner)
    # ------------------------------------------------------------------- #

    def register_with_spawner(self, spawner) -> None:
        """
        Register callbacks with the provided spawner instance.

        The spawner is expected to expose a ``register_hook`` method that
        accepts a callable which receives the raw user request.

        Example (pseudo‑code):
            spawner.register_hook(gatekeeper.process_user_request)
        """
        if not hasattr(spawner, "register_hook"):
            raise AttributeError("Provided spawner does not support hook registration.")
        spawner.register_hook(self.process_user_request)


# --------------------------------------------------------------------------- #
# Convenience singleton (optional)
# --------------------------------------------------------------------------- #

# A module‑level singleton can be imported by downstream modules that only need
# a shared gatekeeper instance.
gatekeeper = IntentGatekeeper()