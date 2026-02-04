"""
atomizer.py
-----------

Utility for converting a high‑level feature plan into a set of minimal, 
parallelizable atomic tasks together with a dependency graph.

The implementation follows the *Atomizer Node* description in
`SWARM_ARCHITECTURE_V2.md`.  It provides:

* `atomize_plan(plan: dict) -> Tuple[List[Task], DependencyGraph]`
* `calculate_parallelism_groups(graph: DependencyGraph) -> List[Set[str]]`
* `export_to_json(tasks, graph, groups) -> str`

The module is deliberately self‑contained – it only depends on the
standard library (json, dataclasses, typing, collections).  This makes it
safe to import from any experiment script without pulling in heavy
runtime dependencies.

Typical usage::

    from atomizer import atomize_plan, export_to_json

    # `feature_plan` is a user‑defined dict describing the workflow.
    tasks, graph = atomize_plan(feature_plan)
    groups = calculate_parallelism_groups(graph)
    json_output = export_to_json(tasks, graph, groups)
    print(json_output)

"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Task:
    """
    Represents a single atomic unit of work.

    Attributes
    ----------
    id: str
        Unique identifier for the task.
    name: str
        Human readable name (usually mirrors the feature name).
    command: str
        The executable command or function signature that will be run.
    inputs: List[str]
        IDs of tasks whose outputs are required.
    outputs: List[str]
        IDs of data artefacts produced by this task.
    meta: Dict[str, Any]
        Optional free‑form metadata (e.g., resource hints).
    """
    id: str
    name: str
    command: str
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


# Dependency graph is a mapping from a task ID to the set of IDs it depends on.
DependencyGraph = Dict[str, Set[str]]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _generate_task_id(base: str, counter: int) -> str:
    """Create a deterministic, unique task ID."""
    return f"{base}_{counter}"


def _topological_sort(graph: DependencyGraph) -> List[str]:
    """
    Perform Kahn's algorithm to produce a topological ordering.
    Raises ValueError if a cycle is detected.
    """
    indegree = {node: 0 for node in graph}
    for deps in graph.values():
        for dep in deps:
            indegree[dep] = indegree.get(dep, 0) + 1

    # Queue of nodes with zero indegree
    zero_indeg = deque([n for n, d in indegree.items() if d == 0])
    order: List[str] = []

    while zero_indeg:
        node = zero_indeg.popleft()
        order.append(node)
        for succ in graph.get(node, []):
            indegree[succ] -= 1
            if indegree[succ] == 0:
                zero_indeg.append(succ)

    if len(order) != len(graph):
        raise ValueError("Cyclic dependency detected in task graph.")
    return order


# ---------------------------------------------------------------------------
# Core atomizer logic
# ---------------------------------------------------------------------------

def atomize_plan(plan: Dict[str, Any]) -> Tuple[List[Task], DependencyGraph]:
    """
    Convert a high‑level feature plan into atomic tasks and a dependency graph.

    The expected ``plan`` structure (simplified)::

        {
            "features": [
                {
                    "name": "feature_a",
                    "command": "python train_a.py",
                    "depends_on": ["feature_b", "feature_c"],
                    "outputs": ["model_a.pkl"],
                    "meta": {...}
                },
                ...
            ]
        }

    Returns
    -------
    tasks : List[Task]
        All generated atomic tasks.
    graph : DependencyGraph
        Mapping ``task_id -> set(task_ids it depends on)``.
    """
    if "features" not in plan or not isinstance(plan["features"], list):
        raise ValueError("Plan must contain a 'features' list.")

    tasks: List[Task] = []
    graph: DependencyGraph = {}
    name_to_task_id: Dict[str, str] = {}

    # First pass – create tasks and record IDs
    for idx, feature in enumerate(plan["features"]):
        if "name" not in feature or "command" not in feature:
            raise ValueError("Each feature must contain at least 'name' and 'command'.")

        task_id = _generate_task_id(feature["name"], idx)
        name_to_task_id[feature["name"]] = task_id

        task = Task(
            id=task_id,
            name=feature["name"],
            command=feature["command"],
            inputs=feature.get("depends_on", []),  # will be resolved to IDs later
            outputs=feature.get("outputs", []),
            meta=feature.get("meta", {})
        )
        tasks.append(task)
        graph[task_id] = set()  # placeholder for dependencies

    # Second pass – resolve dependencies to task IDs
    for task in tasks:
        resolved_deps: Set[str] = set()
        for dep_name in task.inputs:
            if dep_name not in name_to_task_id:
                raise ValueError(f"Undefined dependency '{dep_name}' for task '{task.id}'.")
            resolved_deps.add(name_to_task_id[dep_name])
        graph[task.id] = resolved_deps

    return tasks, graph


def calculate_parallelism_groups(graph: DependencyGraph) -> List[Set[str]]:
    """
    Determine groups of tasks that can be executed in parallel.

    The algorithm walks the graph level‑by‑level (breadth‑first) and groups
    tasks whose dependencies have all been satisfied in previous levels.

    Returns
    -------
    groups : List[Set[str]]
        Ordered list where each set contains task IDs that may run concurrently.
    """
    # Compute in‑degree for each node
    indegree = {node: 0 for node in graph}
    reverse_adj: Dict[str, Set[str]] = defaultdict(set)  # node -> dependants
    for node, deps in graph.items():
        indegree[node] = len(deps)
        for dep in deps:
            reverse_adj[dep].add(node)

    # Kahn's algorithm variant that records layers
    ready = deque([n for n, d in indegree.items() if d == 0])
    groups: List[Set[str]] = []

    while ready:
        current_layer: Set[str] = set()
        for _ in range(len(ready)):
            node = ready.popleft()
            current_layer.add(node)
            for succ in reverse_adj.get(node, []):
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    ready.append(succ)
        groups.append(current_layer)

    # Verify that all nodes were scheduled
    if sum(len(g) for g in groups) != len(graph):
        raise ValueError("Cycle detected while calculating parallelism groups.")
    return groups


def export_to_json(
    tasks: List[Task],
    graph: DependencyGraph,
    groups: List[Set[str]] | None = None,
    indent: int = 2
) -> str:
    """
    Serialize the atomization result to a JSON string.

    The JSON schema::

        {
            "tasks": [{... task dict ...}, ...],
            "dependency_graph": {"task_id": ["dep_id", ...], ...},
            "parallelism_groups": [["task_id", ...], ...]   # optional
        }

    Parameters
    ----------
    tasks
        List of :class:`Task` objects.
    graph
        Dependency graph as returned by :func:`atomize_plan`.
    groups
        Optional pre‑computed parallelism groups.
    indent
        JSON indentation level for readability.

    Returns
    -------
    str
        JSON representation.
    """
    task_dicts = [asdict(t) for t in tasks]
    # Convert sets to sorted lists for deterministic JSON output
    graph_serializable = {k: sorted(v) for k, v in graph.items()}
    payload: Dict[str, Any] = {
        "tasks": task_dicts,
        "dependency_graph": graph_serializable,
    }
    if groups is not None:
        payload["parallelism_groups"] = [sorted(list(g)) for g in groups]

    return json.dumps(payload, indent=indent, sort_keys=True)


# ---------------------------------------------------------------------------
# Simple CLI for ad‑hoc testing (optional, does not affect library usage)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import sys
    import yaml  # PyYAML is optional; if unavailable we fall back to JSON.

    parser = argparse.ArgumentParser(
        description="Atomize a feature plan into tasks and dependency graph."
    )
    parser.add_argument(
        "plan_path",
        type=str,
        help="Path to a YAML or JSON file describing the feature plan."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="-",
        help="Write JSON output to file (default: stdout)."
    )
    args = parser.parse_args()

    # Load plan (YAML preferred)
    try:
        import yaml  # type: ignore
        loader = yaml.safe_load
    except Exception:
        loader = json.load

    try:
        with open(args.plan_path, "r") as fh:
            plan_data = loader(fh)
    except Exception as exc:
        sys.stderr.write(f"Failed to load plan: {exc}\\n")
        sys.exit(1)

    try:
        tasks, dep_graph = atomize_plan(plan_data)
        groups = calculate_parallelism_groups(dep_graph)
        result_json = export_to_json(tasks, dep_graph, groups)
    except Exception as exc:
        sys.stderr.write(f"Atomization error: {exc}\\n")
        sys.exit(1)

    if args.output == "-":
        sys.stdout.write(result_json + "\\n")
    else:
        with open(args.output, "w") as out_fh:
            out_fh.write(result_json + "\\n")