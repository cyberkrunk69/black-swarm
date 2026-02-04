"""
feature_planner.py

A lightweight planner that creates a detailed implementation plan for a single
feature.  The planner can be instantiated per‑feature and run in parallel
(e.g. via threading or multiprocessing).  When the planner cannot progress it
consults an ``ExpertNode`` – a pluggable component that can provide guidance,
suggestions, or missing information.

Typical usage:

    from feature_planner import FeaturePlanner, ExpertNode

    expert = ExpertNode()                     # custom implementation
    planner = FeaturePlanner(
        feature_name="User authentication",
        description="Add login/logout with JWT tokens",
        expert=expert,
    )
    plan = planner.run()
    print(plan)

The output ``plan`` is a multi‑section string that includes:
    * Overview
    * Sub‑tasks (ordered)
    * Dependencies
    * Risks & mitigations
    * Rough timeline
"""

from __future__ import annotations

import json
import textwrap
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Helper / placeholder for the Expert Node
# --------------------------------------------------------------------------- #
class ExpertNode:
    """
    Minimal stub for an Expert Node.  In the real system this would be a
    sophisticated service (LLM, knowledge‑base, etc.) that can answer
    queries about a feature.  The ``ask`` method receives a free‑form prompt
    and returns a string answer.
    """

    def ask(self, prompt: str) -> str:
        # Placeholder implementation – just echo the prompt with a note.
        return f"[ExpertNode] I have no specific knowledge for: {prompt!r}"


# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #
@dataclass
class SubTask:
    title: str
    description: str
    estimated_hours: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "estimated_hours": self.estimated_hours,
            "dependencies": self.dependencies,
        }


@dataclass
class FeaturePlan:
    feature_id: str
    name: str
    overview: str
    sub_tasks: List[SubTask] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    timeline: Optional[str] = None
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_markdown(self) -> str:
        lines = [
            f"# Implementation Plan – {self.name}",
            f"*Feature ID:* `{self.feature_id}`",
            f"*Generated:* {self.generated_at}",
            "",
            "## Overview",
            self.overview,
            "",
            "## Sub‑tasks",
        ]

        for idx, task in enumerate(self.sub_tasks, start=1):
            lines.extend(
                [
                    f"### {idx}. {task.title}",
                    task.description,
                    f"- **Estimated hours:** {task.estimated_hours or 'TBD'}",
                    f"- **Depends on:** {', '.join(task.dependencies) or 'None'}",
                    "",
                ]
            )

        lines.append("## Risks & Mitigations")
        if self.risks:
            for risk in self.risks:
                lines.append(f"- {risk}")
        else:
            lines.append("- None identified")
        lines.append("")

        lines.append("## Timeline")
        lines.append(self.timeline or "TBD")
        lines.append("")

        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "feature_id": self.feature_id,
                "name": self.name,
                "overview": self.overview,
                "sub_tasks": [t.to_dict() for t in self.sub_tasks],
                "risks": self.risks,
                "timeline": self.timeline,
                "generated_at": self.generated_at,
            },
            indent=2,
        )


# --------------------------------------------------------------------------- #
# Planner implementation
# --------------------------------------------------------------------------- #
class FeaturePlanner:
    """
    Generates a detailed implementation plan for a single feature.
    The planner is deliberately stateless except for the injected ``expert``
    which can be consulted when information is missing.
    """

    def __init__(
        self,
        feature_name: str,
        description: str,
        expert: Optional[ExpertNode] = None,
        max_iterations: int = 10,
    ) -> None:
        self.feature_name = feature_name
        self.description = description.strip()
        self.expert = expert or ExpertNode()
        self.max_iterations = max_iterations
        self._plan: Optional[FeaturePlan] = None

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def run(self) -> str:
        """
        Executes the planning loop and returns a markdown representation of
        the plan.
        """
        self._plan = self._create_initial_plan()
        for iteration in range(self.max_iterations):
            if self._is_plan_complete():
                break
            self._refine_plan(iteration)
        else:
            # Max iterations reached – warn the user
            self._append_risk(
                "Planner reached max iterations without reaching a stable plan."
            )
        return self._plan.to_markdown()

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    def _create_initial_plan(self) -> FeaturePlan:
        """
        Build a skeletal plan using only the supplied description.
        """
        feature_id = str(uuid.uuid4())
        overview = self.description
        # Very naive split – look for sentences that start with an action verb.
        # In a real system we would use NLP; here we keep it simple.
        possible_tasks = self._extract_possible_tasks(self.description)

        sub_tasks = [
            SubTask(
                title=task["title"],
                description=task["description"],
                estimated_hours=None,
                dependencies=task["depends_on"],
            )
            for task in possible_tasks
        ]

        return FeaturePlan(
            feature_id=feature_id,
            name=self.feature_name,
            overview=overview,
            sub_tasks=sub_tasks,
            risks=[],
            timeline=None,
        )

    def _extract_possible_tasks(self, text: str) -> List[Dict[str, Any]]:
        """
        Very lightweight heuristic to turn bullet‑like sentences into tasks.
        """
        lines = [ln.strip("- ").strip() for ln in text.splitlines() if ln.strip()]
        tasks: List[Dict[str, Any]] = []
        for line in lines:
            # Assume format: "<verb> <object> ..."
            verb = line.split()[0] if line.split() else "Implement"
            title = verb.capitalize() + " " + " ".join(line.split()[1:5])
            description = line
            tasks.append(
                {
                    "title": title,
                    "description": description,
                    "depends_on": [],  # initially unknown
                }
            )
        return tasks

    def _is_plan_complete(self) -> bool:
        """
        Determines if the plan is “complete”.  For this stub we consider a plan
        complete when every sub‑task has an estimated hour count.
        """
        if not self._plan:
            return False
        return all(t.estimated_hours is not None for t in self._plan.sub_tasks)

    def _refine_plan(self, iteration: int) -> None:
        """
        Attempts to fill missing information (estimates, dependencies,
        timeline, risks) by asking the ExpertNode.
        """
        assert self._plan is not None

        # 1. Estimate missing hours
        for task in self._plan.sub_tasks:
            if task.estimated_hours is None:
                prompt = (
                    f"Estimate the implementation effort in hours for the following "
                    f"sub‑task: \"{task.title}\" – {task.description}"
                )
                answer = self.expert.ask(prompt)
                est = self._parse_estimate(answer)
                task.estimated_hours = est

        # 2. Identify dependencies if not already set
        for task in self._plan.sub_tasks:
            if not task.dependencies:
                prompt = (
                    f"Based on the sub‑task \"{task.title}\", list any other sub‑tasks "
                    f"from this feature that must be completed first."
                )
                answer = self.expert.ask(prompt)
                deps = self._parse_dependencies(answer)
                task.dependencies = deps

        # 3. Generate risks after first iteration
        if iteration == 0:
            prompt = (
                f"Given the feature \"{self.feature_name}\" and its sub‑tasks, "
                f"enumerate up to three potential risks and brief mitigations."
            )
            answer = self.expert.ask(prompt)
            risks = self._parse_risks(answer)
            for r in risks:
                self._append_risk(r)

        # 4. Rough timeline after we have estimates
        if all(t.estimated_hours for t in self._plan.sub_tasks):
            total_hours = sum(t.estimated_hours or 0 for t in self._plan.sub_tasks)
            weeks = max(1, round(total_hours / 40))  # assume 40h/week
            timeline = f"Estimated {total_hours} h of work → approx. {weeks} week(s)."
            self._plan.timeline = timeline

    # ------------------------------------------------------------------- #
    # Parsing helpers – very tolerant, fall back to defaults
    # ------------------------------------------------------------------- #
    def _parse_estimate(self, text: str) -> int:
        """
        Extract a number from the expert answer.  If parsing fails, return 8h as
        a generic placeholder.
        """
        import re

        match = re.search(r"(\d+)\s*(hours?|hrs?)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # fallback: look for any integer
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else 8

    def _parse_dependencies(self, text: str) -> List[str]:
        """
        Expect a comma‑separated list of sub‑task titles.  Return empty list on
        failure.
        """
        if not text:
            return []
        # Remove any surrounding commentary
        cleaned = text.strip().strip(".")
        parts = [p.strip() for p in cleaned.split(",")]
        # Keep only non‑empty strings
        return [p for p in parts if p]

    def _parse_risks(self, text: str) -> List[str]:
        """
        Split on newlines or bullet characters.
        """
        lines = [ln.strip("-• ").strip() for ln in text.splitlines() if ln.strip()]
        return lines

    def _append_risk(self, risk: str) -> None:
        assert self._plan is not None
        self._plan.risks.append(risk)


# --------------------------------------------------------------------------- #
# Convenience entry point for command‑line usage
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate a detailed implementation plan for a single feature."
    )
    parser.add_argument("name", help="Feature name")
    parser.add_argument(
        "description_file",
        help="Path to a text file containing the feature description",
    )
    args = parser.parse_args()

    try:
        with open(args.description_file, "r", encoding="utf-8") as f:
            description = f.read()
    except Exception as e:
        sys.stderr.write(f"Failed to read description file: {e}\\n")
        sys.exit(1)

    planner = FeaturePlanner(feature_name=args.name, description=description)
    markdown_plan = planner.run()
    print(markdown_plan)