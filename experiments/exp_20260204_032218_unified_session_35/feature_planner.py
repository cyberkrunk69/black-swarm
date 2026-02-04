"""
feature_planner.py

A lightweight planner that generates a detailed implementation plan for a single
feature.  The planner can be instantiated per feature and run in parallel
(e.g., via threading or multiprocessing).  When the planner cannot determine
the next step it can query an external "Expert Node" – a callable supplied at
initialisation – to obtain guidance.

The output is a structured dictionary that can be rendered as markdown,
JSON, or any other format required by downstream components.
"""

from __future__ import annotations
import json
import threading
from typing import Any, Callable, Dict, List, Optional, Union

# Type alias for the expert callback.
# It receives the current partial plan and returns a suggestion or None.
ExpertCallback = Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]


class FeaturePlanner:
    """
    Generates a step‑by‑step implementation plan for a single feature.

    Example usage
    -------------
    >>> def mock_expert(partial):
    ...     # Simple fallback that suggests a generic step if none exist.
    ...     if not partial.get("steps"):
    ...         return {"action": "define_requirements", "detail": "Gather user stories"}
    ...     return None
    >>> planner = FeaturePlanner(
    ...     feature_name="User authentication",
    ...     description="Implement login, logout and password reset.",
    ...     expert_callback=mock_expert,
    ... )
    >>> plan = planner.run()
    >>> print(json.dumps(plan, indent=2))
    """

    def __init__(
        self,
        feature_name: str,
        description: str,
        expert_callback: Optional[ExpertCallback] = None,
        max_iterations: int = 25,
        verbose: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        feature_name: str
            Human readable name of the feature.
        description: str
            Brief description of what the feature should achieve.
        expert_callback: Optional[Callable[[dict], Optional[dict]]]
            Function that receives the current partial plan and returns a suggestion.
            If ``None`` the planner will raise an exception when stuck.
        max_iterations: int
            Safety guard to avoid infinite loops.
        verbose: bool
            If True, prints intermediate steps to stdout.
        """
        self.feature_name = feature_name
        self.description = description
        self.expert_callback = expert_callback
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Internal state
        self.plan: Dict[str, Any] = {
            "feature": self.feature_name,
            "description": self.description,
            "steps": [],  # List of ordered step dicts
        }

        # Simple lock for thread‑safety when used in parallel contexts.
        self._lock = threading.Lock()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> Dict[str, Any]:
        """
        Execute the planning loop until a complete plan is produced or the
        iteration limit is reached.

        Returns
        -------
        dict
            The finalized plan.
        """
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            if self.verbose:
                print(f"[{self.feature_name}] Iteration {iteration}")

            # 1️⃣ Try to infer the next step using built‑in heuristics.
            next_step = self._infer_next_step()

            # 2️⃣ If heuristics fail, fall back to the expert node.
            if next_step is None and self.expert_callback:
                if self.verbose:
                    print(f"[{self.feature_name}] Consulting expert node...")
                suggestion = self.expert_callback(self.plan)
                if suggestion:
                    next_step = suggestion

            # 3️⃣ If still no step, abort – we are stuck.
            if next_step is None:
                raise RuntimeError(
                    f"Planner for '{self.feature_name}' is stuck after {iteration} iterations."
                )

            # 4️⃣ Append the step in a thread‑safe manner.
            with self._lock:
                self.plan["steps"].append(next_step)

            # 5️⃣ Check for completion criteria.
            if self._is_complete():
                if self.verbose:
                    print(f"[{self.feature_name}] Planning complete.")
                break

        return self.plan

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _infer_next_step(self) -> Optional[Dict[str, Any]]:
        """
        Very lightweight heuristic engine that looks at the current steps and
        decides what could logically follow.  This stub can be replaced with a
        more sophisticated LLM or rule‑based system.

        Returns
        -------
        dict or None
            A step dictionary or None if the heuristic cannot determine a step.
        """
        steps = self.plan["steps"]
        if not steps:
            return {"action": "gather_requirements", "detail": "Collect user stories and acceptance criteria."}

        last_action = steps[-1]["action"]

        # Simple deterministic flow – expand as needed.
        flow_map = {
            "gather_requirements": {"action": "design_api", "detail": "Sketch REST endpoints and data models."},
            "design_api": {"action": "write_tests", "detail": "Create unit and integration test outlines."},
            "write_tests": {"action": "implement_logic", "detail": "Develop core business logic."},
            "implement_logic": {"action": "code_review", "detail": "Peer review the implementation."},
            "code_review": {"action": "deploy_staging", "detail": "Deploy to staging environment for QA."},
            "deploy_staging": {"action": "release", "detail": "Promote to production after verification."},
        }

        return flow_map.get(last_action)

    def _is_complete(self) -> bool:
        """
        Determines whether the plan is considered complete.  By default the plan
        is complete when the last step's action is ``release``.
        """
        if not self.plan["steps"]:
            return False
        return self.plan["steps"][-1]["action"] == "release"

    # --------------------------------------------------------------------- #
    # Convenience serialization helpers
    # --------------------------------------------------------------------- #
    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Serialize the current plan to a JSON string.
        """
        return json.dumps(self.plan, indent=indent)

    def to_markdown(self) -> str:
        """
        Render the plan as a human‑readable markdown checklist.
        """
        lines = [
            f"# Feature Plan: {self.feature_name}",
            "",
            f"**Description:** {self.description}",
            "",
            "## Implementation Steps",
            "",
        ]
        for idx, step in enumerate(self.plan["steps"], start=1):
            lines.append(f"- [ ] **Step {idx}:** {step['action'].replace('_', ' ').title()} – {step.get('detail', '')}")
        return "\n".join(lines)


# ------------------------------------------------------------------------- #
# Example entry‑point for manual testing (not executed during import)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple demo that runs the planner with a mock expert fallback.
    def dummy_expert(partial_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # If we somehow reach a state with no known next action, suggest a generic final step.
        if not partial_plan["steps"] or partial_plan["steps"][-1]["action"] != "release":
            return {"action": "release", "detail": "Finalize and ship the feature."}
        return None

    planner = FeaturePlanner(
        feature_name="User Authentication",
        description="Implement login, logout, password reset, and session management.",
        expert_callback=dummy_expert,
        verbose=True,
    )
    final_plan = planner.run()
    print("\n=== JSON Plan ===")
    print(planner.to_json())
    print("\n=== Markdown Plan ===")
    print(planner.to_markdown())