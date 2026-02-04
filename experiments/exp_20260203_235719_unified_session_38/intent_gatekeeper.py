"""
Intent Gatekeeper – Conversational Requirements Gathering

This module implements the "Intent Gatekeeper" node described in
SWARM_ARCHITECTURE_V2.md.  Its purpose is to interactively collect
high‑level intent from a user, ask clarifying questions, confirm the
understanding, and finally emit a concise requirements document.

Typical usage (CLI):
    python -m intent_gatekeeper

The script will:
1. Greet the user and request a short description of the desired system.
2. Iterate through a curated list of clarifying questions.
3. Summarise the collected answers.
4. Ask the user to confirm the summary.
5. If confirmed, write a `requirements_<timestamp>.md` file in the same
   directory; otherwise, allow the user to edit answers.

The implementation is deliberately lightweight – no external
dependencies beyond the Python standard library – to keep the node
portable across all experiment environments.
"""

import datetime
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #


@dataclass
class RequirementAnswer:
    """Stores a single question/answer pair."""
    question: str
    answer: str = ""


@dataclass
class RequirementsDocument:
    """Aggregates all collected answers and renders a markdown document."""
    title: str
    description: str
    answers: List[RequirementAnswer] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render the requirements as a human‑readable markdown string."""
        lines = [
            f"# {self.title}",
            "",
            f"**Generated:** {datetime.datetime.now().isoformat()}",
            "",
            "## High‑Level Description",
            self.description,
            "",
            "## Clarifying Answers",
        ]
        for idx, ans in enumerate(self.answers, start=1):
            lines.extend(
                [
                    f"### {idx}. {ans.question}",
                    ans.answer,
                    "",
                ]
            )
        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize the document to JSON – useful for downstream automation."""
        return json.dumps(
            {
                "title": self.title,
                "description": self.description,
                "answers": [asdict(a) for a in self.answers],
                "generated_at": datetime.datetime.now().isoformat(),
            },
            indent=2,
        )


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #


class IntentGatekeeper:
    """
    Conversational engine that drives the requirements‑gathering session.
    """

    DEFAULT_QUESTIONS = [
        "What is the primary goal or problem the system should solve?",
        "Who are the intended users or stakeholders?",
        "What are the key functional capabilities required?",
        "Are there any non‑functional constraints (performance, security, compliance, etc.)?",
        "What platforms or environments must the system operate in?",
        "Do you have any preferred technologies, languages, or frameworks?",
        "What is the expected timeline or major milestones?",
        "Are there any existing systems that this solution must integrate with?",
        "What are the success criteria or measurable outcomes?",
    ]

    def __init__(self, questions: Optional[List[str]] = None):
        self.questions = [RequirementAnswer(q) for q in (questions or self.DEFAULT_QUESTIONS)]
        self.title: str = "Project Requirements"
        self.description: str = ""

    # ------------------------------------------------------------------- #
    # Interaction helpers
    # ------------------------------------------------------------------- #

    @staticmethod
    def _prompt(message: str) -> str:
        """Simple wrapper around input() for easier testing/mocking."""
        return input(message).strip()

    def _collect_initial_description(self) -> None:
        print("\n=== Intent Gatekeeper ===\n")
        self.title = self._prompt("Enter a short title for the project (default: Project Requirements): ") or self.title
        self.description = self._prompt(
            "Provide a brief, high‑level description of the desired system:\n> "
        )
        if not self.description:
            print("⚠️  Description cannot be empty. Please try again.")
            self._collect_initial_description()

    def _ask_clarifying_questions(self) -> None:
        print("\n--- Clarifying Questions ---\n")
        for qa in self.questions:
            answer = self._prompt(f"{qa.question}\n> ")
            while not answer:
                print("⚠️  Answer cannot be empty. Please provide a response.")
                answer = self._prompt(f"{qa.question}\n> ")
            qa.answer = answer

    def _review_and_confirm(self, doc: RequirementsDocument) -> bool:
        print("\n--- Review Summary ---\n")
        print(doc.to_markdown())
        print("\nDo you confirm that the above captures your intent? (y/n)")
        while True:
            resp = self._prompt("> ").lower()
            if resp in {"y", "yes"}:
                return True
            if resp in {"n", "no"}:
                return False
            print("Please answer with 'y' (yes) or 'n' (no).")

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def run(self) -> RequirementsDocument:
        """Execute the full conversational flow and return the final document."""
        self._collect_initial_description()
        self._ask_clarifying_questions()
        doc = RequirementsDocument(
            title=self.title,
            description=self.description,
            answers=self.questions,
        )
        confirmed = self._review_and_confirm(doc)
        if not confirmed:
            print("\nYou chose to restart the session. Let's begin again.\n")
            # Reset answers and restart
            for qa in self.questions:
                qa.answer = ""
            return self.run()
        return doc

    @staticmethod
    def _write_output(doc: RequirementsDocument, output_dir: Path) -> Path:
        """Write both markdown and JSON representations to the given directory."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        md_path = output_dir / f"requirements_{timestamp}.md"
        json_path = output_dir / f"requirements_{timestamp}.json"

        md_path.write_text(doc.to_markdown(), encoding="utf-8")
        json_path.write_text(doc.to_json(), encoding="utf-8")

        return md_path

    def execute(self, output_dir: Optional[Path] = None) -> Path:
        """
        Run the gatekeeper and persist the output.

        Parameters
        ----------
        output_dir: Path | None
            Directory where the requirements files will be saved.
            Defaults to the directory containing this script.

        Returns
        -------
        Path to the generated markdown file.
        """
        output_dir = output_dir or Path(__file__).parent
        doc = self.run()
        md_path = self._write_output(doc, output_dir)
        print(f"\n✅ Requirements document generated: {md_path}")
        return md_path


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Entry‑point for ``python -m intent_gatekeeper``.
    Allows optional command‑line argument to specify an output directory.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive Intent Gatekeeper – gather requirements via conversation."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Directory to store the generated requirements files (default: script directory).",
    )
    args = parser.parse_args()
    gatekeeper = IntentGatekeeper()
    gatekeeper.execute(output_dir=args.output)


if __name__ == "__main__":
    # When executed as a script, launch the interactive session.
    main()