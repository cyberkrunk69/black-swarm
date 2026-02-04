"""
intent_gatekeeper.py
--------------------

Conversational Requirements Gathering Node.

The Intent Gatekeeper is responsible for:
* Interacting with a user (or upstream node) to collect a clear, unambiguous
  specification of the desired functionality.
* Asking clarifying questions until the intent is sufficiently understood.
* Confirming the captured intent with the user.
* Producing a concise, machine‑readable requirements document.

The implementation follows the flow described in
`SWARM_ARCHITECTURE_V2.md` under the **Intent Gatekeeper Node** section.

Typical usage:

    from intent_gatekeeper import IntentGatekeeper

    gatekeeper = IntentGatekeeper()
    # feed user messages one‑by‑one
    response = gatekeeper.process_message("I need a script that backs up my DB.")
    print(response)   # -> asks clarifying question
    # ... continue feeding messages until gatekeeper.is_complete() is True
    requirements = gatekeeper.get_requirements()
    print(requirements)   # -> JSON/YAML style document

"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class GatekeeperState(Enum):
    """Finite‑state machine states for the gatekeeper."""
    INITIAL = auto()
    GATHERING = auto()
    CONFIRMING = auto()
    COMPLETED = auto()


@dataclass
class ClarifyingQuestion:
    """A single clarifying question."""
    key: str                     # internal identifier for the answer
    question: str                # text presented to the user
    answer: Optional[str] = None # filled once user responds


@dataclass
class RequirementsDocument:
    """Structured representation of the final requirements."""
    title: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    acceptance_criteria: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return a plain‑dict suitable for JSON/YAML serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "parameters": self.parameters,
            "acceptance_criteria": self.acceptance_criteria,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the document to a pretty‑printed JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class IntentGatekeeper:
    """
    Conversational requirements gathering engine.

    The gatekeeper maintains a list of clarifying questions.  It iteratively
    presents the next unanswered question, records the answer, and when all
    required fields are populated asks the user for confirmation.  If the user
    rejects the summary, the gatekeeper re‑enters the gathering phase.
    """

    # Template of questions – can be extended per project.
    _question_template: List[ClarifyingQuestion] = [
        ClarifyingQuestion(
            key="title",
            question="What is a concise title for the feature or script you need?",
        ),
        ClarifyingQuestion(
            key="description",
            question="Please provide a short description of the desired functionality.",
        ),
        ClarifyingQuestion(
            key="parameters",
            question=(
                "List any input parameters the solution should accept. "
                "Provide them as `name: type` pairs, one per line."
            ),
        ),
        ClarifyingQuestion(
            key="acceptance_criteria",
            question=(
                "What are the acceptance criteria? "
                "List each criterion on a separate line."
            ),
        ),
    ]

    def __init__(self) -> None:
        self.state: GatekeeperState = GatekeeperState.INITIAL
        # Deep‑copy the template so each instance has its own mutable list.
        self.questions: List[ClarifyingQuestion] = [
            ClarifyingQuestion(q.key, q.question) for q in self._question_template
        ]
        self.requirements: Optional[RequirementsDocument] = None

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def process_message(self, user_message: str) -> str:
        """
        Handle an incoming user message and return the next system reply.

        The method drives the internal state machine:
        * INITIAL -> GATHERING (first question)
        * GATHERING -> GATHERING (next unanswered question)
        * GATHERING -> CONFIRMING (once all answers collected)
        * CONFIRMING -> COMPLETED (if user confirms) or back to GATHERING
          (if user rejects or asks to modify).
        """
        if self.state == GatekeeperState.INITIAL:
            self.state = GatekeeperState.GATHERING
            return self._next_question()

        if self.state == GatekeeperState.GATHERING:
            self._record_answer(user_message)
            if self._all_answered():
                self.state = GatekeeperState.CONFIRMING
                return self._confirmation_prompt()
            else:
                return self._next_question()

        if self.state == GatekeeperState.CONFIRMING:
            normalized = user_message.strip().lower()
            if normalized in {"yes", "y", "confirm"}:
                self._finalize_requirements()
                self.state = GatekeeperState.COMPLETED
                return (
                    "Great! The requirements have been captured.\n"
                    "You can retrieve them with `gatekeeper.get_requirements()`."
                )
            elif normalized in {"no", "n", "reject", "restart"}:
                # Reset answers but keep the question list intact.
                for q in self.questions:
                    q.answer = None
                self.state = GatekeeperState.GATHERING
                return (
                    "Understood. Let's start over.\n"
                    + self._next_question()
                )
            else:
                # Anything else is treated as a request to edit a specific field.
                return (
                    "I didn't understand your response. Please reply with "
                    "'yes' to accept the summary or 'no' to restart."
                )

        if self.state == GatekeeperState.COMPLETED:
            return "Requirements are already finalized. Use `get_requirements()` to view them."

        # Fallback – should never happen
        return "Unexpected state. Please restart the session."

    def is_complete(self) -> bool:
        """Return True when the requirements document has been finalized."""
        return self.state == GatekeeperState.COMPLETED

    def get_requirements(self) -> Optional[RequirementsDocument]:
        """
        Return the finalized RequirementsDocument, or None if not yet completed.
        """
        return self.requirements

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _next_question(self) -> str:
        """Return the next unanswered question."""
        for q in self.questions:
            if q.answer is None:
                return q.question
        # Should not reach here because caller checks _all_answered()
        return "All questions answered."

    def _record_answer(self, answer: str) -> None:
        """
        Store the user's answer to the current pending question.
        The first unanswered question in the list receives the answer.
        """
        for q in self.questions:
            if q.answer is None:
                q.answer = answer.strip()
                break

    def _all_answered(self) -> bool:
        """Check whether every question has an answer."""
        return all(q.answer is not None for q in self.questions)

    def _confirmation_prompt(self) -> str:
        """Build a human‑readable summary and ask for confirmation."""
        summary_lines = [
            "Please review the captured requirements:",
            "",
            f"**Title:** {self._get_answer('title')}",
            f"**Description:** {self._get_answer('description')}",
            "",
            "**Parameters:**",
            self._format_multiline(self._get_answer('parameters')),
            "",
            "**Acceptance Criteria:**",
            self._format_multiline(self._get_answer('acceptance_criteria')),
            "",
            "Is this correct? (yes/no)",
        ]
        return "\n".join(summary_lines)

    def _get_answer(self, key: str) -> str:
        """Retrieve the stored answer for a given key."""
        for q in self.questions:
            if q.key == key:
                return q.answer or ""
        return ""

    @staticmethod
    def _format_multiline(text: str) -> str:
        """Indent multiline user input for nicer display."""
        if not text:
            return "  (none provided)"
        lines = text.splitlines()
        return "\n".join(f"  - {line.strip()}" for line in lines if line.strip())

    def _finalize_requirements(self) -> None:
        """Convert collected answers into a RequirementsDocument."""
        # Parse parameters and acceptance criteria into structured forms.
        parameters = self._parse_key_value_block(self._get_answer("parameters"))
        acceptance = self._parse_list_block(self._get_answer("acceptance_criteria"))

        self.requirements = RequirementsDocument(
            title=self._get_answer("title"),
            description=self._get_answer("description"),
            parameters=parameters,
            acceptance_criteria=acceptance,
        )

    @staticmethod
    def _parse_key_value_block(block: str) -> Dict[str, str]:
        """
        Convert a block like:
            host: string
            port: int
        into a dict { "host": "string", "port": "int" }.
        Empty lines are ignored.
        """
        result: Dict[str, str] = {}
        for line in block.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                # Fallback – store the whole line as a key with empty type.
                result[line] = ""
                continue
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
        return result

    @staticmethod
    def _parse_list_block(block: str) -> List[str]:
        """
        Convert a multiline block into a list of stripped strings.
        Empty lines are ignored.
        """
        return [line.strip() for line in block.splitlines() if line.strip()]

# -------------------------------------------------------------------------
# Example interactive loop (for manual testing only; not executed in production)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    gatekeeper = IntentGatekeeper()
    print("Intent Gatekeeper started. Type your messages below.")
    while not gatekeeper.is_complete():
        user_input = input("> ")
        reply = gatekeeper.process_message(user_input)
        print(reply)

    print("\n--- Final Requirements Document (JSON) ---")
    print(gatekeeper.get_requirements().to_json())