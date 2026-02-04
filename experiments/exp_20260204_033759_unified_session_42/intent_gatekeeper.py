"""
Intent Gatekeeper Node

This module implements a conversational requirements‑gathering assistant.
Its purpose is to interact with a user (or upstream node) to clarify the
intention behind a request before any further processing is performed.

Key behaviours (as described in SWARM_ARCHITECTURE_V2.md):
* Prompt the user for an initial description of the desired outcome.
* Iteratively ask targeted clarifying questions until the assistant
  determines that it has a sufficient understanding of the request.
* Summarise the gathered information into a clear, structured requirements
  document.
* Require explicit user confirmation that the summary is correct before
  signalling completion.

The implementation below is deliberately lightweight and uses standard
input/output, making it suitable for both interactive CLI usage and unit
testing (by injecting a custom I/O handler).

Usage example (CLI):
    $ python intent_gatekeeper.py
    > Please describe what you would like to achieve:
    ...

The generated requirements document is returned as a dictionary and also
printed in a human‑readable format.
"""

from __future__ import annotations
import json
import sys
from typing import Callable, Dict, List, Optional, Tuple

# Type alias for I/O functions – makes the class testable.
IOHandler = Tuple[Callable[[str], None], Callable[[], str]]  # (print_func, input_func)


class IntentGatekeeper:
    """
    Conversational requirements‑gathering engine.

    Parameters
    ----------
    io_handler: optional tuple of (print_func, input_func)
        Allows redirection of I/O for testing. Defaults to (print, input).
    max_iterations: int
        Upper bound on the number of clarification rounds to avoid infinite loops.
    """

    def __init__(
        self,
        io_handler: Optional[IOHandler] = None,
        max_iterations: int = 10,
    ) -> None:
        self.print, self.input = io_handler if io_handler else (print, input)
        self.max_iterations = max_iterations
        self.requirements: Dict[str, str] = {}
        self._clarification_questions: List[Tuple[str, str]] = []  # (question, key)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> Dict[str, str]:
        """Execute the full conversation and return the final requirements dict."""
        self._greet()
        self._collect_initial_intent()
        self._clarify_intent()
        self._summarize_and_confirm()
        return self.requirements

    # --------------------------------------------------------------------- #
    # Conversation steps
    # --------------------------------------------------------------------- #
    def _greet(self) -> None:
        self.print("=== Intent Gatekeeper ===")
        self.print(
            "I will ask a few questions to make sure I fully understand "
            "what you want to achieve before proceeding."
        )

    def _collect_initial_intent(self) -> None:
        description = self.input(
            "\nPlease describe the overall goal or outcome you are looking for:\n> "
        ).strip()
        self.requirements["goal_description"] = description

    def _clarify_intent(self) -> None:
        """
        Iteratively ask clarifying questions. The set of questions is generated
        based on the current knowledge state. For simplicity, we use a static
        list of common aspects; a real implementation could be driven by an LLM
        or a rules engine.
        """
        # Define a static questionnaire – can be extended later.
        self._clarification_questions = [
            ("What are the primary inputs or data sources required?", "inputs"),
            ("What should the output look like? (format, content, etc.)", "outputs"),
            ("Are there any constraints (time, resources, compliance)?", "constraints"),
            ("Who are the intended users or stakeholders?", "stakeholders"),
            ("Do you have any preferred technologies or libraries?", "technologies"),
        ]

        iteration = 0
        for question, key in self._clarification_questions:
            if iteration >= self.max_iterations:
                self.print("\nMaximum clarification rounds reached. Proceeding with gathered info.")
                break
            answer = self.input(f"\n{question}\n> ").strip()
            if answer:
                self.requirements[key] = answer
                iteration += 1

    def _summarize_and_confirm(self) -> None:
        """Present a formatted requirements document and ask for confirmation."""
        self.print("\n--- Requirements Summary ---")
        for key, value in self.requirements.items():
            self.print(f"{key.replace('_', ' ').title()}: {value}")

        while True:
            confirmation = self.input(
                "\nIs this summary correct? (yes/no)\n> "
            ).strip().lower()
            if confirmation in ("yes", "y"):
                self.print("\nRequirements confirmed. Proceeding.")
                break
            elif confirmation in ("no", "n"):
                self.print("\nLet's refine the requirements.")
                self._refine_requirements()
                # After refinement, loop back to confirmation.
            else:
                self.print("Please answer with 'yes' or 'no'.")

    def _refine_requirements(self) -> None:
        """
        Simple refinement loop: ask the user which section needs changes,
        then re‑prompt for that specific field.
        """
        fields = list(self.requirements.keys())
        field_str = ", ".join(f"{i+1}:{f}" for i, f in enumerate(fields))
        while True:
            choice = self.input(
                f"\nEnter the number of the field you want to edit (or 'done' to finish):\n{field_str}\n> "
            ).strip().lower()
            if choice == "done":
                break
            if not choice.isdigit():
                self.print("Invalid input – please enter a number or 'done'.")
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(fields):
                key = fields[idx]
                new_val = self.input(f"Enter new value for '{key}':\n> ").strip()
                if new_val:
                    self.requirements[key] = new_val
                    self.print(f"Updated '{key}'.")
                else:
                    self.print("No change made.")
                # Continue allowing further edits until user types 'done'.
            else:
                self.print("Number out of range.")

    # --------------------------------------------------------------------- #
    # Utility
    # --------------------------------------------------------------------- #
    @staticmethod
    def to_json(requirements: Dict[str, str]) -> str:
        """Serialize the requirements dict to a pretty‑printed JSON string."""
        return json.dumps(requirements, indent=2, sort_keys=True)


# -------------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    gatekeeper = IntentGatekeeper()
    final_requirements = gatekeeper.run()
    # Output JSON for downstream consumption
    sys.stdout.write("\n=== Final Requirements (JSON) ===\n")
    sys.stdout.write(IntentGatekeeper.to_json(final_requirements) + "\n")