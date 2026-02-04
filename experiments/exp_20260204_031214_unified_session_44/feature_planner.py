"""
feature_planner.py

A lightweight planner that generates a detailed implementation plan for a single
feature.  The planner can be instantiated per feature and run in parallel
with other planners.  When the planner encounters an ambiguous step it can
delegate to an external "Expert Node" (e.g. a LLM or knowledge base) via a
callback that the caller supplies.

The output is a structured dictionary that can be rendered to markdown, JSON,
or any other format the downstream pipeline expects.
"""

from __future__ import annotations

import json
import textwrap
from typing import Callable, Dict, List, Optional, Any


class FeaturePlanner:
    """
    Core planner for a single feature.

    Parameters
    ----------
    feature_name: str
        Human‑readable name of the feature.
    description: str
        High‑level description of what the feature should do.
    expert_callback: Optional[Callable[[str], str]]
        A callable that receives a query string and returns a response.
        Used when the planner cannot resolve a step on its own.
        If ``None`` the planner will raise ``RuntimeError`` on ambiguous steps.
    """

    def __init__(
        self,
        feature_name: str,
        description: str,
        expert_callback: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.feature_name = feature_name
        self.description = description
        self.expert_callback = expert_callback
        self._plan: List[Dict[str, Any]] = []

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def generate_plan(self) -> Dict[str, Any]:
        """
        Build a detailed implementation plan.

        Returns
        -------
        dict
            A dictionary with the following shape:
            {
                "feature": <feature_name>,
                "description": <description>,
                "steps": [
                    {
                        "id": <int>,
                        "title": <short title>,
                        "details": <detailed description>,
                        "subtasks": [<optional list of strings>],
                        "dependencies": [<list of step ids>],
                        "status": "pending"
                    },
                    ...
                ]
            }
        """
        self._plan.clear()
        self._add_introduction()
        self._add_data_model()
        self._add_api_layer()
        self._add_business_logic()
        self._add_tests()
        self._add_documentation()
        return {
            "feature": self.feature_name,
            "description": self.description,
            "steps": self._plan,
        }

    def render_markdown(self) -> str:
        """
        Render the generated plan as a human‑readable markdown document.
        """
        plan = self.generate_plan()
        lines = [
            f"# Implementation Plan – {plan['feature']}",
            "",
            f"**Description:** {plan['description']}",
            "",
            "## Steps",
            "",
        ]
        for step in plan["steps"]:
            lines.append(f"### {step['id']}. {step['title']}")
            lines.append("")
            lines.append(textwrap.indent(step["details"], "    "))
            if step.get("subtasks"):
                lines.append("")
                lines.append("**Sub‑tasks:**")
                for sub in step["subtasks"]:
                    lines.append(f"- {sub}")
            if step.get("dependencies"):
                deps = ", ".join(str(d) for d in step["dependencies"])
                lines.append("")
                lines.append(f"**Depends on:** {deps}")
            lines.append("")
        return "\n".join(lines)

    def render_json(self) -> str:
        """
        Return the plan as a JSON string (pretty‑printed).
        """
        return json.dumps(self.generate_plan(), indent=2, sort_keys=False)

    # --------------------------------------------------------------------- #
    # Internal helpers – each adds a step to ``self._plan``
    # --------------------------------------------------------------------- #
    def _add_step(
        self,
        title: str,
        details: str,
        subtasks: Optional[List[str]] = None,
        dependencies: Optional[List[int]] = None,
    ) -> None:
        step_id = len(self._plan) + 1
        self._plan.append(
            {
                "id": step_id,
                "title": title,
                "details": details,
                "subtasks": subtasks or [],
                "dependencies": dependencies or [],
                "status": "pending",
            }
        )

    def _add_introduction(self) -> None:
        details = (
            f"Create a high‑level overview of **{self.feature_name}**. "
            "Identify the primary use‑cases, success criteria, and any "
            "non‑functional requirements (performance, security, scalability)."
        )
        self._add_step("Feature Overview", details)

    def _add_data_model(self) -> None:
        details = (
            "Design the data model required for the feature. "
            "If the domain entities are unclear, query the Expert Node."
        )
        if "model" not in self.description.lower():
            # Example of consulting the expert node
            if self.expert_callback:
                query = f"Suggest a data model for feature '{self.feature_name}'."
                response = self.expert_callback(query)
                details += f"\n\n**Expert suggestion:**\n{response}"
            else:
                raise RuntimeError(
                    "Data model ambiguous and no expert_callback provided."
                )
        self._add_step("Data Model Design", details)

    def _add_api_layer(self) -> None:
        details = (
            "Define the public API (REST, GraphQL, RPC, etc.) that exposes the "
            "feature's functionality. Include endpoint signatures, request/response "
            "schemas, authentication/authorization requirements, and error handling."
        )
        self._add_step("API Specification", details, dependencies=[2])

    def _add_business_logic(self) -> None:
        details = (
            "Implement core business logic. Break the implementation into "
            "atomic functions/classes that map to the data model and API layer. "
            "Identify any external services or libraries needed."
        )
        self._add_step(
            "Business Logic Implementation",
            details,
            dependencies=[2, 3],
        )

    def _add_tests(self) -> None:
        details = (
            "Write unit, integration, and end‑to‑end tests covering all code paths. "
            "Create test fixtures for the data model and mock external services. "
            "Define acceptance criteria that match the success criteria from the overview."
        )
        self._add_step("Testing Strategy & Implementation", details, dependencies=[4])

    def _add_documentation(self) -> None:
        details = (
            "Generate developer documentation (docstrings, architecture diagram, "
            "API reference) and user‑facing docs (README, usage examples). "
            "Ensure the docs are version‑controlled alongside the code."
        )
        self._add_step("Documentation", details, dependencies=[5])

    # --------------------------------------------------------------------- #
    # Utility – for external callers
    # --------------------------------------------------------------------- #
    @staticmethod
    def load_from_json(json_str: str) -> Dict[str, Any]:
        """
        Helper to deserialize a plan JSON string back into a dict.
        """
        return json.loads(json_str)


# ------------------------------------------------------------------------- #
# Example usage (not executed during import)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple stub expert that echoes the query – replace with a real LLM call.
    def dummy_expert(query: str) -> str:
        return f"[Expert response to: '{query}']"

    planner = FeaturePlanner(
        feature_name="User Profile Service",
        description="Provide CRUD operations for user profiles, with avatar upload.",
        expert_callback=dummy_expert,
    )
    print(planner.render_markdown())
    # Or JSON:
    # print(planner.render_json())