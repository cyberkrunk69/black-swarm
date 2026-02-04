"""
intent_gatekeeper.py

Core component of the unified session architecture.  It captures the
user's original intent, makes it available to downstream nodes, and
periodically validates that the system remains aligned with that intent.

The implementation is deliberately lightweight – it provides a clear API
that the spawner (and any future nodes) can import without requiring any
modifications to read‑only core files.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# --------------------------------------------------------------------------- #
# Intent Data Structure
# --------------------------------------------------------------------------- #
@dataclass
class Intent:
    """
    Structured representation of a user's request.

    Attributes
    ----------
    goal: str
        Primary objective the user wants to achieve.
    constraints: List[str]
        Hard limits that must not be violated (e.g., time, resources).
    preferences: List[str]
        Soft preferences that guide how the goal should be met.
    anti_goals: List[str]
        Things the user explicitly does *not* want.
    clarifications: List[str] = field(default_factory=list)
        Follow‑up questions or notes that arise during processing.
    """
    goal: str
    constraints: List[str]
    preferences: List[str]
    anti_goals: List[str]
    clarifications: List[str] = field(default_factory=list)

    def to_prompt_block(self) -> str:
        """
        Render the intent as a concise, machine‑readable block that can be
        prefixed to any downstream prompt.
        """
        block = [
            "=== USER INTENT START ===",
            f"Goal: {self.goal}",
            f"Constraints: {'; '.join(self.constraints) if self.constraints else 'None'}",
            f"Preferences: {'; '.join(self.preferences) if self.preferences else 'None'}",
            f"Anti‑Goals: {'; '.join(self.anti_goals) if self.anti_goals else 'None'}",
            f"Clarifications: {'; '.join(self.clarifications) if self.clarifications else 'None'}",
            "=== USER INTENT END ===",
        ]
        return "\n".join(block)


# --------------------------------------------------------------------------- #
# Global Intent Store
# --------------------------------------------------------------------------- #
_current_intent: Optional[Intent] = None
_intent_lock = threading.Lock()


def set_intent(intent: Intent) -> None:
    """Thread‑safe setter for the global intent."""
    global _current_intent
    with _intent_lock:
        _current_intent = intent


def get_intent() -> Optional[Intent]:
    """Thread‑safe getter for the global intent."""
    with _intent_lock:
        return _current_intent


# --------------------------------------------------------------------------- #
# Parsing Utilities
# --------------------------------------------------------------------------- #
_SECTION_REGEX = re.compile(
    r"(?P<header>Goal|Constraints|Preferences|Anti[- ]Goals|Clarifications)[:\s]+(?P<content>.+?)(?=(?:\n[A-Z]|$))",
    re.IGNORECASE | re.DOTALL,
)


def _clean_list(text: str) -> List[str]:
    """Split a semi‑colon or newline separated string into a list of trimmed items."""
    if not text:
        return []
    # Replace common separators with a single newline then split
    normalized = re.sub(r"[;,]\s*", "\n", text.strip())
    return [item.strip() for item in normalized.splitlines() if item.strip()]


def parse_intent(raw_text: str) -> Intent:
    """
    Very simple heuristic parser that extracts intent sections from free‑form
    user text.  It looks for headings like ``Goal:``, ``Constraints:``, etc.
    If a heading is missing, the whole text is treated as the goal.

    Parameters
    ----------
    raw_text: str
        The raw user request.

    Returns
    -------
    Intent
        Structured representation of the extracted intent.
    """
    matches = {m["header"].lower(): m["content"].strip() for m in _SECTION_REGEX.finditer(raw_text)}

    # Fallback: if no explicit headings, treat the entire request as the goal.
    goal = matches.get("goal")
    if not goal:
        goal = raw_text.strip()

    constraints = _clean_list(matches.get("constraints", ""))
    preferences = _clean_list(matches.get("preferences", ""))
    anti_goals = _clean_list(matches.get("anti-goals", ""))
    clarifications = _clean_list(matches.get("clarifications", ""))

    intent = Intent(
        goal=goal,
        constraints=constraints,
        preferences=preferences,
        anti_goals=anti_goals,
        clarifications=clarifications,
    )
    set_intent(intent)
    return intent


# --------------------------------------------------------------------------- #
# Injection Helper
# --------------------------------------------------------------------------- #
def inject_intent_into_prompt(prompt: str, intent: Optional[Intent] = None) -> str:
    """
    Prefix the given prompt with a formatted intent block.  If ``intent`` is
    omitted, the currently stored global intent is used.

    Parameters
    ----------
    prompt: str
        The downstream prompt that will be sent to the LLM.
    intent: Intent, optional
        Specific intent to inject; defaults to the global intent.

    Returns
    -------
    str
        Prompt with the intent block prepended.
    """
    if intent is None:
        intent = get_intent()
    if intent is None:
        # No intent captured yet – return the prompt unchanged.
        return prompt
    return f"{intent.to_prompt_block()}\n\n{prompt}"


# --------------------------------------------------------------------------- #
# Alignment Checker
# --------------------------------------------------------------------------- #
def _intent_alignment_score(state_snapshot: Dict[str, Any], intent: Intent) -> float:
    """
    Compute a naïve alignment score between the current system state and the
    original intent.  The function is intentionally simple – it looks for
    keyword overlap with the goal and checks that none of the constraints are
    violated.

    Returns a value in [0.0, 1.0] where 1.0 means perfect alignment.
    """
    # Simple keyword presence check for the goal.
    goal_keywords = set(re.findall(r"\w+", intent.goal.lower()))
    state_text = " ".join(str(v) for v in state_snapshot.values()).lower()
    present = sum(1 for kw in goal_keywords if kw in state_text)
    goal_score = present / len(goal_keywords) if goal_keywords else 1.0

    # Constraints are treated as "must not appear" in the state.
    constraint_violations = sum(
        1 for c in intent.constraints if c.lower() in state_text
    )
    constraint_score = 1.0 - (constraint_violations / len(intent.constraints)) if intent.constraints else 1.0

    # Combine scores (weighted equally for now)
    return (goal_score + constraint_score) / 2.0


def check_alignment(state_snapshot: Dict[str, Any]) -> bool:
    """
    Public API used by downstream nodes to verify alignment.  Returns ``True``
    if the alignment score is above a configurable threshold (default 0.75).

    Parameters
    ----------
    state_snapshot: Dict[str, Any]
        Arbitrary snapshot of the current execution context (e.g., generated
        text, selected actions, etc.).

    Returns
    -------
    bool
        ``True`` if still aligned with the original intent.
    """
    intent = get_intent()
    if intent is None:
        # No intent captured – assume aligned.
        return True

    score = _intent_alignment_score(state_snapshot, intent)
    THRESHOLD = 0.75
    return score >= THRESHOLD


# --------------------------------------------------------------------------- #
# Background Alignment Monitor (optional)
# --------------------------------------------------------------------------- #
class AlignmentMonitor(threading.Thread):
    """
    Background thread that periodically checks alignment against a user‑provided
    state supplier callable.  When misalignment is detected it logs a warning
    (or could raise an exception in a stricter deployment).
    """

    def __init__(self, state_supplier: callable, interval: float = 5.0):
        """
        Parameters
        ----------
        state_supplier: callable -> Dict[str, Any]
            Function that returns the latest execution snapshot.
        interval: float
            Seconds between checks.
        """
        super().__init__(daemon=True)
        self.state_supplier = state_supplier
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = self.state_supplier()
                if not check_alignment(snapshot):
                    # In a real system this could trigger a corrective action.
                    print("[IntentGatekeeper] WARNING: Detected drift from original intent.")
            except Exception as exc:  # pragma: no cover
                print(f"[IntentGatekeeper] Alignment monitor error: {exc}")
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()


# --------------------------------------------------------------------------- #
# Integration Hook for Spawner
# --------------------------------------------------------------------------- #
def initialize_intent_gatekeeper(state_supplier: callable, start_monitor: bool = True) -> None:
    """
    Convenience function for the spawner to set up the gatekeeper.

    Parameters
    ----------
    state_supplier: callable
        Callable returning a snapshot of the current system state.
    start_monitor: bool
        Whether to launch the background alignment monitor.
    """
    if start_monitor:
        monitor = AlignmentMonitor(state_supplier)
        monitor.start()
        # Store the monitor on the module for potential later shutdown.
        globals()["_alignment_monitor"] = monitor


__all__ = [
    "Intent",
    "parse_intent",
    "inject_intent_into_prompt",
    "check_alignment",
    "initialize_intent_gatekeeper",
    "AlignmentMonitor",
]