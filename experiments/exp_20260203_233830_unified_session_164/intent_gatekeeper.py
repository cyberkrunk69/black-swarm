"""Intent Gatekeeper Module

This module provides the first node in the unified architecture – the
Intent Gatekeeper. It parses incoming user requests, extracts a structured
`Intent` object, and ensures that downstream prompts stay aligned with the
original intent.

Key responsibilities:
1. Parse a raw user request into a structured Intent.
2. Store the original intent for the lifetime of a session.
3. Inject the intent into every downstream prompt.
4. Periodically verify alignment with the original intent.

The implementation is deliberately lightweight and does not depend on any
external libraries beyond the Python standard library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Callable, Any, Optional


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Intent:
    """Structured representation of a user's intent."""

    goal: str = ""
    constraints: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    anti_goals: List[str] = field(default_factory=list)
    clarifications: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """An Intent is truthy if it contains at least a goal."""
        return bool(self.goal)


# --------------------------------------------------------------------------- #
# Parsing utilities
# --------------------------------------------------------------------------- #
_SECTION_REGEX = re.compile(
    r"(?P<header>Goal|Constraints|Preferences|Anti[- ]Goals|Clarifications?)\s*[:\-]\s*(?P<body>.+?)(?=(\n[A-Z][a-z]+[:\-])|\Z)",
    re.IGNORECASE | re.DOTALL,
)


def _clean_list(text: str) -> List[str]:
    """Split a block of text into a list of trimmed strings."""
    # Split on newlines or commas, ignore empty entries
    items = re.split(r"[\n,]+", text)
    return [item.strip() for item in items if item.strip()]


def parse_intent(request: str) -> Intent:
    """
    Parse a raw user request into an ``Intent`` instance.

    The parser looks for headings such as ``Goal:``, ``Constraints:``,
    ``Preferences:``, ``Anti-Goals:``, and ``Clarifications:``.  Anything
    that cannot be matched is placed into the ``clarifications`` field.

    Parameters
    ----------
    request:
        The raw user request string.

    Returns
    -------
    Intent
        The extracted intent.
    """
    intent = Intent()
    found_sections = set()

    for match in _SECTION_REGEX.finditer(request):
        header = match.group("header").strip().lower()
        body = match.group("body").strip()

        if header.startswith("goal"):
            intent.goal = body
            found_sections.add("goal")
        elif header.startswith("constraint"):
            intent.constraints = _clean_list(body)
            found_sections.add("constraints")
        elif header.startswith("preference"):
            intent.preferences = _clean_list(body)
            found_sections.add("preferences")
        elif header.startswith("anti"):
            intent.anti_goals = _clean_list(body)
            found_sections.add("anti_goals")
        elif header.startswith("clarification"):
            intent.clarifications = _clean_list(body)
            found_sections.add("clarifications")

    # Anything that wasn't captured as a known section is treated as a
    # clarification (fallback).
    if not found_sections:
        # No explicit headings – treat the whole request as a goal.
        intent.goal = request.strip()
    else:
        # Capture any leftover text after the last known section.
        # This is a simple heuristic: anything after the final match that
        # does not start a new heading is added to clarifications.
        last_match_end = max(m.end() for m in _SECTION_REGEX.finditer(request))
        leftover = request[last_match_end:].strip()
        if leftover:
            intent.clarifications.extend(_clean_list(leftover))

    return intent


# --------------------------------------------------------------------------- #
# Injection & alignment utilities
# --------------------------------------------------------------------------- #
def _format_intent_block(intent: Intent) -> str:
    """Render the Intent as a textual block that can be prefixed to prompts."""
    lines = ["--- Intent Summary ---"]
    if intent.goal:
        lines.append(f"Goal: {intent.goal}")
    if intent.constraints:
        lines.append(f"Constraints: {', '.join(intent.constraints)}")
    if intent.preferences:
        lines.append(f"Preferences: {', '.join(intent.preferences)}")
    if intent.anti_goals:
        lines.append(f"Anti-Goals: {', '.join(intent.anti_goals)}")
    if intent.clarifications:
        lines.append(f"Clarifications: {', '.join(intent.clarifications)}")
    lines.append("--- End Intent Summary ---")
    return "\n".join(lines)


def inject_intent(prompt: str, intent: Intent) -> str:
    """
    Prepend the intent summary to a downstream prompt.

    Parameters
    ----------
    prompt:
        The original downstream prompt.
    intent:
        The Intent object to inject.

    Returns
    -------
    str
        The new prompt with the intent block at the top.
    """
    intent_block = _format_intent_block(intent)
    return f"{intent_block}\n\n{prompt}"


def check_alignment(current_prompt: str, intent: Intent) -> bool:
    """
    Very lightweight heuristic to verify that a downstream prompt still
    respects the original intent.

    Returns ``True`` if the prompt appears aligned, ``False`` otherwise.
    """
    # Simple heuristic: ensure that the goal (or any constraint) appears in the prompt.
    # This is intentionally cheap; more sophisticated checks can be added later.
    lowered = current_prompt.lower()
    if intent.goal and intent.goal.lower() not in lowered:
        return False
    for c in intent.constraints:
        if c.lower() not in lowered:
            return False
    return True


# --------------------------------------------------------------------------- #
# Gatekeeper class – runtime holder
# --------------------------------------------------------------------------- #
class IntentGatekeeper:
    """
    Runtime component that holds the original intent and provides callbacks
    for spawner integration.
    """

    def __init__(self):
        self.original_intent: Optional[Intent] = None

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def capture_intent(self, user_request: str) -> Intent:
        """Parse and store the intent from the initial user request."""
        self.original_intent = parse_intent(user_request)
        return self.original_intent

    def get_intent(self) -> Intent:
        """Return the stored intent (raises if not set)."""
        if not self.original_intent:
            raise RuntimeError("Intent has not been captured yet.")
        return self.original_intent

    # ------------------------------------------------------------------- #
    # Integration callbacks
    # ------------------------------------------------------------------- #
    def pre_prompt_callback(self, prompt: str) -> str:
        """
        Callback to be executed **before** a downstream prompt is sent to the
        LLM. It injects the intent summary.
        """
        intent = self.get_intent()
        return inject_intent(prompt, intent)

    def post_prompt_callback(self, generated_output: str) -> str:
        """
        Callback to be executed **after** the LLM has produced output. It checks
        alignment and optionally appends a reminder if drift is detected.
        """
        intent = self.get_intent()
        aligned = check_alignment(generated_output, intent)
        if aligned:
            return generated_output
        # Drift detected – prepend a gentle reminder.
        reminder = (
            "\n\n[Reminder] Please ensure the response stays aligned with the original intent "
            "as described above."
        )
        return generated_output + reminder


# --------------------------------------------------------------------------- #
# Spawner integration helper
# --------------------------------------------------------------------------- #
def init_gatekeeper(spawner: Any) -> IntentGatekeeper:
    """
    Initialise the IntentGatekeeper and register its callbacks with the
    provided ``spawner`` object.

    The spawner is expected to expose the following registration methods
    (if they exist):
        - ``register_pre_prompt(callback: Callable[[str], str])``
        - ``register_post_prompt(callback: Callable[[str], str])``

    If a method is missing, the function fails silently – this keeps the
    gatekeeper usable in minimal test environments.
    """
    gatekeeper = IntentGatekeeper()

    # Register pre‑prompt injection
    if hasattr(spawner, "register_pre_prompt"):
        spawner.register_pre_prompt(gatekeeper.pre_prompt_callback)

    # Register post‑prompt alignment check
    if hasattr(spawner, "register_post_prompt"):
        spawner.register_post_prompt(gatekeeper.post_prompt_callback)

    # Expose the gatekeeper on the spawner for external access if desired
    setattr(spawner, "intent_gatekeeper", gatekeeper)

    return gatekeeper


# --------------------------------------------------------------------------- #
# Example usage (for documentation / debugging only – not executed in prod)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simulated user request
    raw = """Goal: Generate a Python script that parses CSV files.
Constraints: Use only the standard library, keep the script under 200 lines.
Preferences: Include type hints, add docstrings.
Anti-Goals: Do not write to disk, avoid external dependencies."""
    kg = IntentGatekeeper()
    intent = kg.capture_intent(raw)
    print("Captured Intent:", intent)

    downstream_prompt = "Write the function body for parse_csv."
    injected = kg.pre_prompt_callback(downstream_prompt)
    print("\nInjected Prompt:\n", injected)

    # Simulate LLM output that violates a constraint
    llm_output = "Here's a script that uses pandas to read CSV files."
    aligned_output = kg.post_prompt_callback(llm_output)
    print("\nPost‑Prompt Check:\n", aligned_output)