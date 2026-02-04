"""Intent Gatekeeper Module

This module defines the core data structures and utilities for capturing,
preserving, and re‑asserting user intent throughout the execution pipeline.
It is deliberately lightweight – heavy‑weight NLP parsing can be swapped in
later without changing the public API.

Key responsibilities:
1. Parse a raw user request into a structured :class:`Intent`.
2. Provide helpers to inject the intent into downstream prompts.
3. Offer a periodic alignment check to guard against drift.

The module is designed to be imported by the experiment's spawner (or any
other component) without side‑effects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Intent:
    """Structured representation of a user's original request.

    Attributes
    ----------
    goal: str
        The primary objective the user wants to achieve.
    constraints: List[str]
        Hard limits or requirements (e.g., time, budget, technology stack).
    preferences: List[str]
        Desired qualities or optional choices (e.g., "use Python", "prefer
        functional style").
    anti_goals: List[str]
        Outcomes the user explicitly wants to avoid.
    clarifications: List[str]
        Follow‑up questions or missing information that need resolution.
    """
    goal: str
    constraints: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    anti_goals: List[str] = field(default_factory=list)
    clarifications: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the Intent to a plain dict (useful for logging)."""
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
            parts.append(f"Anti‑Goals: {', '.join(self.anti_goals)}")
        if self.clarifications:
            parts.append(f"Clarifications: {', '.join(self.clarifications)}")
        return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Parsing utilities
# --------------------------------------------------------------------------- #
_SECTION_REGEX = re.compile(
    r"(?P<header>Goal|Constraints|Preferences|Anti[- ]Goals|Clarifications):\s*(?P<body>.*?)(?=\n[A-Z][a-z]+:|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _split_items(text: str) -> List[str]:
    """Split a free‑form list into trimmed items.

    Supports commas, semicolons, line breaks, or bullet points.
    """
    # Normalize newlines and bullets
    cleaned = re.sub(r"[\r\n]+", "\n", text)
    cleaned = re.sub(r"^[\*\-\·]\s+", "", cleaned, flags=re.MULTILINE)
    # Split on commas, semicolons, or newlines
    items = re.split(r"[,\n;]+", cleaned)
    return [i.strip() for i in items if i.strip()]


def parse_user_request(raw_text: str) -> Intent:
    """Parse a raw user request into an :class:`Intent`.

    The parser looks for explicit section headers (case‑insensitive):
    ``Goal:``, ``Constraints:``, ``Preferences:``, ``Anti‑Goals:``, and
    ``Clarifications:``. Anything before the first header is treated as the goal
    if no explicit ``Goal:`` header is found.

    Parameters
    ----------
    raw_text: str
        The full user message.

    Returns
    -------
    Intent
        Structured representation of the extracted intent.
    """
    sections: Dict[str, str] = {}
    for match in _SECTION_REGEX.finditer(raw_text):
        header = match.group("header").strip().lower()
        body = match.group("body").strip()
        sections[header] = body

    # Goal extraction – explicit header or fallback to first line(s)
    if "goal" in sections:
        goal = sections["goal"]
    else:
        # Take everything up to the first recognized header as the goal
        first_header = _SECTION_REGEX.search(raw_text)
        if first_header:
            goal = raw_text[: first_header.start()].strip()
        else:
            goal = raw_text.strip()

    # Helper to fetch list‑style sections
    def get_list(key: str) -> List[str]:
        raw = sections.get(key, "")
        return _split_items(raw) if raw else []

    intent = Intent(
        goal=goal,
        constraints=get_list("constraints"),
        preferences=get_list("preferences"),
        anti_goals=get_list("anti-goals"),
        clarifications=get_list("clarifications"),
    )
    return intent


# --------------------------------------------------------------------------- #
# Prompt augmentation
# --------------------------------------------------------------------------- #
def inject_intent_into_prompt(prompt: str, intent: Intent) -> str:
    """Prepend a concise intent summary to a downstream prompt.

    This function is idempotent – if the prompt already contains an
    ``[Intent]`` block it will replace it with the latest version.

    Parameters
    ----------
    prompt: str
        The original downstream prompt.
    intent: Intent
        The captured user intent.

    Returns
    -------
    str
        Prompt with an ``[Intent]`` header block.
    """
    intent_block = f"[Intent]\n{intent}\n[End Intent]\n"
    # Detect existing block
    pattern = re.compile(r"\[Intent\].*?\[End Intent\]\n?", re.DOTALL)
    if pattern.search(prompt):
        new_prompt = pattern.sub(intent_block, prompt)
    else:
        new_prompt = intent_block + prompt
    return new_prompt


# --------------------------------------------------------------------------- #
# Alignment checking
# --------------------------------------------------------------------------- #
def check_alignment(current_context: str, intent: Intent) -> bool:
    """Determine whether the current context still aligns with the original intent.

    The heuristic is simple: we verify that the goal phrase (or a close
    synonym) appears in the context and that none of the anti‑goals are
    mentioned. This can be replaced with a more sophisticated model later.

    Parameters
    ----------
    current_context: str
        The latest generated text or plan.
    intent: Intent
        The original intent.

    Returns
    -------
    bool
        ``True`` if alignment looks acceptable, ``False`` otherwise.
    """
    lowered = current_context.lower()
    goal_match = intent.goal.lower() in lowered

    anti_match = any(anti.lower() in lowered for anti in intent.anti_goals)

    # Simple heuristic: goal must be present and no anti‑goal should appear.
    return goal_match and not anti_match


# --------------------------------------------------------------------------- #
# Convenience API for the spawner / downstream components
# --------------------------------------------------------------------------- #
def capture_and_augment(raw_user_input: str, downstream_prompt: str) -> str:
    """One‑stop helper used by the spawner.

    1. Parse the raw user input.
    2. Store the resulting :class:`Intent` (the caller can cache it).
    3. Inject the intent into the downstream prompt.

    Returns
    -------
    str
        Prompt ready for the next LLM call.
    """
    intent = parse_user_request(raw_user_input)
    return inject_intent_into_prompt(downstream_prompt, intent)


# Export symbols for external import
__all__ = [
    "Intent",
    "parse_user_request",
    "inject_intent_into_prompt",
    "check_alignment",
    "capture_and_augment",
]