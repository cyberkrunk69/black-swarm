"""
atomizer.py
-----------

Converts high‑level feature plans into a minimal set of atomic, parallelizable
tasks together with a dependency graph.  The output is a JSON structure
containing:

* ``tasks`` – list of atomic task descriptors
* ``dependency_graph`` – adjacency list where each key is a task id and the
  value is a list of task ids that must complete before the key can run.
* ``parallelism_groups`` – groups of tasks that can be executed concurrently
  (i.e. tasks with no inter‑dependencies).

The implementation follows the *Atomizer Node* description in
`SWARM_ARCHITECTURE_V2.md`.
"""

from __future__ import annotations

import json
import itertools
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple


class Atomizer:
    """
    Core class that transforms a feature plan into atomic tasks and builds a
    dependency graph.

    The expected *feature_plan* format (JSON‑compatible) is a list of feature
    dictionaries, each containing:

    - ``name``: str – human readable name
    - ``steps``: list – ordered list of step dictionaries
        - each step must contain a ``type`` (e.g. "compile", "test", "deploy")
          and optionally a ``depends_on`` list of step identifiers within the
          same feature.

    Example::

        [
            {
                "name": "FeatureA",
                "steps": [
                    {"id": "compile", "type": "compile"},
                    {"id": "unit_test", "type": "test", "depends_on": ["compile"]},
                    {"id": "package", "type": "package", "depends_on": ["unit_test"]}
                ]
            },
            {
                "name": "FeatureB",
                "steps": [
                    {"id": "lint", "type": "lint"},
                    {"id": "integration_test", "type": "test", "depends_on": ["lint"]}
                ]
            }
        ]
    """

    def __init__(self, feature_plan: List[Dict[str, Any]]) -> None:
        self.feature_plan = feature_plan
        self.tasks: List[Dict[str, Any]] = []
        self.dependency_graph: Dict[str, List[str]] = defaultdict(list)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def atomize(self) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]], List[Set[str]]]:
        """
        Main entry point.  Returns a tuple of (tasks, dependency_graph,
        parallelism_groups).
        """
        self._create_atomic_tasks()
        self._build_dependency_graph()
        parallel_groups = self._calculate_parallelism_groups()
        return self.tasks, dict(self.dependency_graph), parallel_groups

    def to_json(self) -> str:
        """
        Serialises the atomization result to a JSON string.
        """
        tasks, graph, groups = self.atomize()
        payload = {
            "tasks": tasks,
            "dependency_graph": graph,
            "parallelism_groups": [list(g) for g in groups],
        }
        return json.dumps(payload, indent=2)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _create_atomic_tasks(self) -> None:
        """
        Flattens the feature plan into a list of atomic tasks.  Each atomic task
        receives a globally unique ``task_id`` (UUID4) and retains enough
        metadata to be scheduled later.
        """
        for feature in self.feature_plan:
            feature_name = feature.get("name", "UnnamedFeature")
            steps = feature.get("steps", [])
            for step in steps:
                # Normalise step identifier – if omitted we generate one.
                step_id = step.get("id") or str(uuid.uuid4())
                atomic_task = {
                    "task_id": f"{feature_name}:{step_id}",
                    "feature": feature_name,
                    "step_id": step_id,
                    "type": step.get("type", "unknown"),
                    "payload": step.get("payload", {}),  # optional data for execution
                }
                self.tasks.append(atomic_task)

    def _build_dependency_graph(self) -> None:
        """
        Populates ``self.dependency_graph`` where each key is a ``task_id`` and
        the value is a list of predecessor ``task_id`` values.
        """
        # Helper to locate a task by (feature, step_id)
        task_lookup: Dict[Tuple[str, str], str] = {
            (t["feature"], t["step_id"]): t["task_id"] for t in self.tasks
        }

        # Iterate over the original plan to respect the declared ``depends_on``.
        for feature in self.feature_plan:
            feature_name = feature.get("name", "UnnamedFeature")
            for step in feature.get("steps", []):
                step_id = step.get("id")
                if not step_id:
                    # If the step didn't have an explicit id we cannot express a
                    # dependency – skip it (it will be treated as independent).
                    continue
                current_task_id = task_lookup[(feature_name, step_id)]
                for dep in step.get("depends_on", []):
                    # Dependency can be expressed as just a step id (same feature)
                    # or as "FeatureName:StepId".
                    if ":" in dep:
                        dep_feature, dep_step = dep.split(":", 1)
                    else:
                        dep_feature, dep_step = feature_name, dep
                    dep_task_id = task_lookup.get((dep_feature, dep_step))
                    if dep_task_id:
                        self.dependency_graph[current_task_id].append(dep_task_id)
                    else:
                        raise ValueError(
                            f"Unresolved dependency '{dep}' for task '{current_task_id}'."
                        )
                # Ensure every task appears in the graph (even if it has no deps)
                self.dependency_graph.setdefault(current_task_id, [])

    def _calculate_parallelism_groups(self) -> List[Set[str]]:
        """
        Determines maximal sets of tasks that can run in parallel.  The algorithm
        performs a topological sort and groups tasks by their distance from the
        source (i.e. level order).  Tasks on the same level have no mutual
        dependencies.
        """
        # Compute in-degree for each node
        in_degree: Dict[str, int] = {node: 0 for node in self.dependency_graph}
        for deps in self.dependency_graph.values():
            for dep in deps:
                in_degree[dep] = in_degree.get(dep, 0) + 1

        # Kahn's algorithm – collect nodes with zero in-degree iteratively.
        zero_in = [node for node, deg in in_degree.items() if deg == 0]
        level_groups: List[Set[str]] = []

        while zero_in:
            current_level = set(zero_in)
            level_groups.append(current_level)

            next_zero = []
            for node in zero_in:
                # Remove edges outgoing from *node*
                for succ in self._successors(node):
                    in_degree[succ] -= 1
                    if in_degree[succ] == 0:
                        next_zero.append(succ)
            zero_in = next_zero

        # Detect cycles (any node left with non‑zero in-degree)
        if any(deg > 0 for deg in in_degree.values()):
            raise RuntimeError("Cyclic dependency detected in the task graph.")

        return level_groups

    def _successors(self, node: str) -> List[str]:
        """
        Helper returning all tasks that depend on ``node``.
        """
        succ = []
        for candidate, deps in self.dependency_graph.items():
            if node in deps:
                succ.append(candidate)
        return succ


# ------------------------------------------------------------------------- #
# CLI Helper – useful for quick manual testing
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Atomize a feature plan.")
    parser.add_argument(
        "plan",
        type=argparse.FileType("r"),
        help="Path to a JSON file containing the feature plan.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Write the resulting JSON to this file (default: stdout).",
    )
    args = parser.parse_args()

    try:
        feature_plan = json.load(args.plan)
    except json.JSONDecodeError as exc:
        parser.error(f"Invalid JSON in plan file: {exc}")

    atomizer = Atomizer(feature_plan)
    result_json = atomizer.to_json()
    args.output.write(result_json + "\n")