"""
feature_planner.py

A lightweight planner that generates a detailed implementation plan for a single
feature. The planner can run in parallel with other planners (one per feature)
and may consult an external "Expert Node" when it encounters uncertainty.

The output is a structured dictionary that can be rendered to markdown,
JSON, or any other format required by downstream tooling.
"""

import json
import threading
import uuid
from typing import Any, Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Helper: Simple Expert Node client (placeholder)
# --------------------------------------------------------------------------- #
class ExpertNodeClient:
    """
    Minimal client to query an external Expert Node. In a real system this
    would perform HTTP calls, RPC, or other IPC mechanisms. Here we provide
    a stub that can be overridden in tests.
    """

    def __init__(self, query_fn: Optional[Callable[[str], str]] = None):
        """
        :param query_fn: Optional custom function that receives a prompt and
                         returns a response string.
        """
        self.query_fn = query_fn or self._default_query

    def _default_query(self, prompt: str) -> str:
        """
        Default stub implementation – simply echoes the prompt.
        Replace with real networking logic as needed.
        """
        return f"[ExpertNode] Received prompt: {prompt}"

    def ask(self, prompt: str) -> str:
        """Send a prompt to the Expert Node and return its answer."""
        return self.query_fn(prompt)


# --------------------------------------------------------------------------- #
# Core Planner
# --------------------------------------------------------------------------- #
class FeaturePlanner:
    """
    Generates a step‑by‑step implementation plan for a given feature.
    The planner is designed to be thread‑safe so multiple instances can run
    concurrently (one per feature).
    """

    def __init__(
        self,
        feature_name: str,
        description: str,
        expert_client: Optional[ExpertNodeClient] = None,
    ):
        """
        :param feature_name: Human readable name of the feature.
        :param description: Short description of what the feature should do.
        :param expert_client: Optional client for consulting the Expert Node.
        """
        self.id = str(uuid.uuid4())
        self.feature_name = feature_name
        self.description = description
        self.expert_client = expert_client or ExpertNodeClient()
        self.plan: List[Dict[str, Any]] = []
        self.lock = threading.Lock()

    # ----------------------------------------------------------------------- #
    # Public API
    # ----------------------------------------------------------------------- #
    def generate_plan(self) -> Dict[str, Any]:
        """
        Main entry point – orchestrates the planning process and returns the
        final plan as a dictionary.
        """
        self._log("Starting plan generation")
        self._add_initial_step()
        self._expand_steps()
        self._finalize_plan()
        self._log("Plan generation completed")
        return self._as_dict()

    # ----------------------------------------------------------------------- #
    # Internal workflow
    # ----------------------------------------------------------------------- #
    def _add_initial_step(self) -> None:
        """Create the first high‑level step based on the description."""
        step = {
            "id": self._new_step_id(),
            "title": f"Understand requirements for {self.feature_name}",
            "description": self.description,
            "status": "pending",
            "substeps": [],
        }
        self._append_step(step)

    def _expand_steps(self) -> None:
        """
        Iteratively refine each pending step. If a step is too vague,
        consult the Expert Node for clarification.
        """
        index = 0
        while index < len(self.plan):
            step = self.plan[index]
            if step["status"] == "pending":
                self._log(f"Expanding step {step['id']}: {step['title']}")
                refined = self._refine_step(step)
                step.update(refined)
            index += 1

    def _refine_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Turn a high‑level step into concrete substeps. If the planner cannot
        infer substeps automatically, it asks the Expert Node.
        """
        # Simple heuristic: split on commas or semicolons.
        raw = step["description"]
        potential_substeps = [
            s.strip() for s in raw.replace(";", ",").split(",") if s.strip()
        ]

        if len(potential_substeps) <= 1:
            # Not enough info – ask expert.
            prompt = (
                f"Provide a detailed implementation breakdown for the feature "
                f"'{self.feature_name}'. Description: {self.description}"
            )
            expert_answer = self.expert_client.ask(prompt)
            # Assume expert returns a JSON list of substep titles.
            try:
                substep_titles = json.loads(expert_answer)
                if not isinstance(substep_titles, list):
                    raise ValueError
            except Exception:
                # Fallback: treat the whole answer as a single substep.
                substep_titles = [expert_answer]

            substeps = [
                {
                    "id": self._new_step_id(),
                    "title": title,
                    "description": "",
                    "status": "pending",
                    "substeps": [],
                }
                for title in substep_titles
            ]
        else:
            substeps = [
                {
                    "id": self._new_step_id(),
                    "title": title,
                    "description": "",
                    "status": "pending",
                    "substeps": [],
                }
                for title in potential_substeps
            ]

        return {"status": "in_progress", "substeps": substeps}

    def _finalize_plan(self) -> None:
        """Mark leaf steps as ready for implementation."""
        def mark_ready(step: Dict[str, Any]) -> None:
            if not step["substeps"]:
                step["status"] = "ready"
            else:
                for sub in step["substeps"]:
                    mark_ready(sub)

        for root in self.plan:
            mark_ready(root)

    # ----------------------------------------------------------------------- #
    # Utility methods
    # ----------------------------------------------------------------------- #
    def _append_step(self, step: Dict[str, Any]) -> None:
        with self.lock:
            self.plan.append(step)

    def _new_step_id(self) -> str:
        return f"step-{uuid.uuid4().hex[:8]}"

    def _as_dict(self) -> Dict[str, Any]:
        return {
            "planner_id": self.id,
            "feature_name": self.feature_name,
            "description": self.description,
            "plan": self.plan,
        }

    def _log(self, message: str) -> None:
        # Simple thread‑safe logger – replace with structured logging if needed.
        print(f"[FeaturePlanner:{self.id[:8]}] {message}")


# --------------------------------------------------------------------------- #
# Example usage (removed in production; kept for reference)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Demonstrate a quick plan generation.
    description = (
        "Create a REST endpoint `/api/v1/items` that supports GET, POST, "
        "and DELETE. Validate input, interact with the database, and return "
        "standard JSON responses."
    )
    planner = FeaturePlanner("Item API", description)
    plan = planner.generate_plan()
    print(json.dumps(plan, indent=2))