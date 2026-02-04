"""
Intent Gatekeeper Node
---------------------

This module implements a conversational *requirements‑gathering* assistant.
Its purpose is to interactively clarify a user's intent before any
generation or execution proceeds.  The flow mirrors the description in
`SWARM_ARCHITECTURE_V2.md` under the **Intent Gatekeeper Node** section.

Key behaviours
--------------
1. **Ask Clarifying Questions** – The assistant probes for essential
   information (purpose, stakeholders, functional & non‑functional
   requirements, constraints, acceptance criteria).

2. **Confirmation Loop** – After each answer the user is asked to confirm
   the captured information.  If the user answers *no*, the question is
   re‑asked.

3. **Requirements Document** – Once all items are confirmed, a clear,
   markdown‑formatted requirements document is produced and printed (or
   optionally saved to a file).

Usage
-----
Run the module directly::

    python intent_gatekeeper.py

The script will guide you through a series of prompts and finally output
the requirements document.

Design
------
* `IntentGatekeeper` – core class handling the conversation state.
* `Question` – simple data holder for a prompt and the captured answer.
* `main()` – entry‑point that instantiates the gatekeeper and runs the
  interactive session.

The implementation is deliberately lightweight and relies only on the
standard library, making it suitable for inclusion in any experiment
workspace.
"""

import sys
from dataclasses import dataclass, field
from typing import List, Callable, Optional


@dataclass
class Question:
    """A single clarifying question."""
    prompt: str
    answer: Optional[str] = None
    confirmed: bool = False


class IntentGatekeeper:
    """
    Conversational requirements‑gathering assistant.

    The gatekeeper walks the user through a predefined set of questions,
    confirming each answer before moving on.  When all items are confirmed,
    it renders a markdown requirements document.
    """

    def __init__(self, input_func: Callable[[str], str] = input, output_func: Callable[[str], None] = print):
        self.input = input_func
        self.output = output_func
        self.questions: List[Question] = self._build_questionnaire()

    @staticmethod
    def _build_questionnaire() -> List[Question]:
        """Define the sequence of clarifying questions."""
        return [
            Question(prompt="1️⃣ What is the overall purpose or goal of the task?"),
            Question(prompt="2️⃣ Who are the primary stakeholders or users?"),
            Question(prompt="3️⃣ List the functional requirements (what the system must do)."),
            Question(prompt="4️⃣ List the non‑functional requirements (performance, security, etc.)."),
            Question(prompt="5️⃣ Are there any constraints (technology, budget, timeline, regulatory)?"),
            Question(prompt="6️⃣ Define the acceptance criteria (how we will know the task is complete)."),
        ]

    def _ask_question(self, q: Question) -> None:
        """Prompt the user for an answer and store it."""
        while True:
            self.output("\n" + q.prompt)
            answer = self.input("> ").strip()
            if not answer:
                self.output("⚠️  Answer cannot be empty. Please provide some details.")
                continue
            q.answer = answer
            if self._confirm(f"Please confirm you entered:\n\"{answer}\" (yes/no): "):
                q.confirmed = True
                break
            else:
                self.output("🔄  Let's try again.")

    @staticmethod
    def _confirm(message: str) -> bool:
        """Simple yes/no confirmation loop."""
        while True:
            resp = input(message).strip().lower()
            if resp in {"yes", "y"}:
                return True
            if resp in {"no", "n"}:
                return False
            print("Please answer with 'yes' or 'no'.")

    def run(self) -> None:
        """Execute the full conversational flow."""
        self.output("\n=== Intent Gatekeeper ===")
        self.output("I will ask a series of clarifying questions to capture the requirements.")
        self.output("You can edit your answers until you confirm each one.\n")

        for q in self.questions:
            self._ask_question(q)

        self.output("\n✅ All items confirmed. Generating requirements document...\n")
        doc = self.render_requirements()
        self.output(doc)

        # Optionally offer to save the document
        if self._confirm("\nWould you like to save the requirements document to a file? (yes/no): "):
            filename = self.input("Enter filename (default: requirements.md): ").strip() or "requirements.md"
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(doc)
                self.output(f"📄 Requirements saved to {filename}")
            except Exception as exc:
                self.output(f"❌ Failed to write file: {exc}")

    def render_requirements(self) -> str:
        """Create a markdown formatted requirements document."""
        lines = [
            "# Requirements Document",
            "",
            "## Purpose",
            self.questions[0].answer,
            "",
            "## Stakeholders",
            self.questions[1].answer,
            "",
            "## Functional Requirements",
            self._format_list(self.questions[2].answer),
            "",
            "## Non‑Functional Requirements",
            self._format_list(self.questions[3].answer),
            "",
            "## Constraints",
            self._format_list(self.questions[4].answer),
            "",
            "## Acceptance Criteria",
            self._format_list(self.questions[5].answer),
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_list(text: str) -> str:
        """
        Convert a free‑form answer into a markdown bullet list.
        If the user already used line breaks, keep them; otherwise split on commas.
        """
        if "\n" in text:
            items = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            items = [item.strip() for item in text.split(",") if item.strip()]

        if not items:
            return "_None provided_"
        return "\n".join(f"- {item}" for item in items)


def main():
    """Entry point for command‑line execution."""
    gatekeeper = IntentGatekeeper()
    try:
        gatekeeper.run()
    except KeyboardInterrupt:
        sys.exit("\n👋 Interaction cancelled by user.")


if __name__ == "__main__":
    main()