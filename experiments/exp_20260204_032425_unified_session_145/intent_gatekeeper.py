"""
Intent Gatekeeper

This module provides utilities to parse a user request into a structured
Intent object, store it, inject it into downstream prompts, and periodically
verify alignment with the original intent.

The module is deliberately lightweight and has no external dependencies beyond
the Python standard library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Intent:
    """Structured representation of a user's original request."""
    goal: str = ""
    constraints: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    anti_goals: List[str] = field(default_factory=list)
    clarifications: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Return a dictionary representation – handy for prompt injection."""
        return {
            "goal": self.goal,
            "constraints": self.constraints,
            "preferences": self.preferences,
            "anti_goals": self.anti_goals,
            "clarifications": self.clarifications,
        }

    def __str__(self) -> str:
        parts = [f"Goal: {self.goal}"]
        if self.constraints:
            parts.append(f"Constraints: {', '.join(self.constraints)}")
        if self.preferences:
            parts.append(f"Preferences: {', '.join(self.preferences)}")
        if self.anti_goals:
            parts.append(f"Anti-Goals: {', '.join(self.anti_goals)}")
        if self.clarifications:
            parts.append(f"Clarifications: {', '.join(self.clarifications)}")
        return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Parsing utilities
# --------------------------------------------------------------------------- #

_SECTION_REGEX = re.compile(
    r"(?P<header>Goal|Constraints?|Preferences?|Anti[-\s]?Goals?):\s*(?P<body>.+?)(?=\n[A-Z][a-z]+:|$)",
    re.IGNORECASE | re.DOTALL,
)


def _split_items(text: str) -> List[str]:
    """Split a comma‑ or newline‑separated list into clean strings."""
    items = re.split(r",|\n", text)
    return [itm.strip() for itm in items if itm.strip()]


def parse_user_request(request: str) -> Intent:
    """
    Parse a raw user request into an :class:`Intent`.

    The parser looks for sections prefixed with keywords such as
    ``Goal:``, ``Constraints:``, ``Preferences:``, and ``Anti-Goals:``.
    Anything not captured is placed into ``clarifications`` for later follow‑up.

    Example input::

        Goal: Generate a monthly sales report.
        Constraints: Use only data from the last 12 months, no external APIs.
        Preferences: Output as a PDF, include charts.
        Anti-Goals: Do not expose raw data.

    Returns:
        Intent: populated with extracted values.
    """
    intent = Intent()
    matches = list(_SECTION_REGEX.finditer(request))

    captured_headers = set()
    for match in matches:
        header = match.group("header").strip().lower()
        body = match.group("body").strip()
        captured_headers.add(header)

        if header.startswith("goal"):
            intent.goal = body
        elif header.startswith("constraint"):
            intent.constraints = _split_items(body)
        elif header.startswith("preference"):
            intent.preferences = _split_items(body)
        elif header.startswith("anti"):
            intent.anti_goals = _split_items(body)

    # Anything not captured as a known section is treated as a clarification.
    # We remove the captured sections from the original text and keep the rest.
    remaining = request
    for match in matches:
        remaining = remaining.replace(match.group(0), "")
    remaining = remaining.strip()
    if remaining:
        intent.clarifications = _split_items(remaining)

    return intent


# --------------------------------------------------------------------------- #
# Prompt injection utilities
# --------------------------------------------------------------------------- #

def inject_intent_into_prompt(prompt: str, intent: Intent) -> str:
    """
    Prepend a concise, machine‑readable representation of the intent to a prompt.

    The intent is injected as a JSON‑like block surrounded by triple backticks,
    making it easy for downstream LLM calls to recognise and respect it.

    Example::

        ```intent
        {
            "goal": "...",
            "constraints": [...],
            "preferences": [...],
            "anti_goals": [...]
        }
        ```

    Args:
        prompt: The original prompt that will be sent downstream.
        intent: The :class:`Intent` object to embed.

    Returns:
        A new prompt string with the intent block prepended.
    """
    import json

    intent_block = json.dumps(intent.as_dict(), ensure_ascii=False, indent=2)
    injected = f"```intent\n{intent_block}\n```\n\n{prompt}"
    return injected


# --------------------------------------------------------------------------- #
# Alignment checking
# --------------------------------------------------------------------------- #

def check_alignment(current_output: str, intent: Intent) -> bool:
    """
    Very lightweight heuristic to verify that the current output still aligns
    with the original intent.

    Checks performed:
        * Goal keyword presence (case‑insensitive substring).
        * Absence of any anti‑goal phrase.
        * All constraints appear in the output (simple substring check).

    Returns:
        True if alignment looks acceptable, False otherwise.
    """
    lowered = current_output.lower()

    # Goal must be mentioned (best‑effort)
    if intent.goal and intent.goal.lower() not in lowered:
        return False

    # Anti‑goals must NOT appear
    for anti in intent.anti_goals:
        if anti.lower() in lowered:
            return False

    # All constraints should be respected
    for const in intent.constraints:
        if const.lower() not in lowered:
            # If a constraint is a negative statement ("do not ...") we flip logic
            if const.lower().startswith("do not") or const.lower().startswith("no "):
                if const.lower().replace("do not ", "").replace("no ", "") in lowered:
                    return False
            else:
                return False

    return True


# --------------------------------------------------------------------------- #
# Integration hook for the spawner (read‑only core)
# --------------------------------------------------------------------------- #

def register_intent_gatekeeper(spawner: Any) -> None:
    """
    Register the gatekeeper's callbacks with a spawner instance.

    The spawner is expected to expose the following hook points:
        * `on_user_message(callback)` – called with the raw user message.
        * `on_prompt_build(callback)` – called with the prompt before it is sent
          downstream; should return the possibly‑modified prompt.
        * `on_response(callback)` – called with the LLM's raw response; can be
          used to perform alignment checks.

    This function does not modify the spawner; it merely attaches callbacks.
    """
    # Store the parsed intent globally for the session
    session_state = {"intent": None}

    def handle_user_message(message: str):
        session_state["intent"] = parse_user_request(message)

    def handle_prompt_build(prompt: str) -> str:
        intent = session_state.get("intent")
        if intent:
            return inject_intent_into_prompt(prompt, intent)
        return prompt

    def handle_response(response: str) -> str:
        intent = session_state.get("intent")
        if intent and not check_alignment(response, intent):
            # Simple fallback – prepend a reminder of the original intent.
            reminder = f"Reminder of original intent:\n{intent}"
            return f"{reminder}\n\n{response}"
        return response

    # Attach callbacks if the spawner provides the expected methods.
    if hasattr(spawner, "on_user_message"):
        spawner.on_user_message(handle_user_message)
    if hasattr(spawner, "on_prompt_build"):
        spawner.on_prompt_build(handle_prompt_build)
    if hasattr(spawner, "on_response"):
        spawner.on_response(handle_response)


# --------------------------------------------------------------------------- #
# Convenience export
# --------------------------------------------------------------------------- #

__all__ = [
    "Intent",
    "parse_user_request",
    "inject_intent_into_prompt",
    "check_alignment",
    "register_intent_gatekeeper",
]