"""
atomizer.py

Converts high‑level feature plans into a minimal set of atomic tasks,
produces a dependency graph, and groups tasks that can be executed in
parallel.

The implementation follows the “Atomizer Node” description in
SWARM_ARCHITECTURE_V2.md.

Typical usage:

    from atomizer import atomize_plan, dump_graph
    plan = {...}                     # user‑provided feature plan
    tasks, graph = atomize_plan(plan)
    dump_graph(tasks, graph, "graph.json")
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple


# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
class AtomicTask:
    """
    Minimal representation of an executable unit.

    Attributes
    ----------
    id: str
        Unique identifier for the task.
    action: str
        Name of the primitive operation (e.g., "fetch_data", "train_model").
    params: dict
        Parameters required for the action.
    depends_on: Set[str]
        IDs of tasks that must finish before this task can start.
    """

    __slots__ = ("id", "action", "params", "depends_on")

    def __init__(self, task_id: str, action: str, params: Dict[str, Any] | None = None):
        self.id = task_id
        self.action = action
        self.params = params or {}
        self.depends_on: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "params": self.params,
            "depends_on": list(self.depends_on),
        }

    def __repr__(self) -> str:
        return f"<AtomicTask {self.id!r} action={self.action!r} deps={list(self.depends_on)!r}>"


# ----------------------------------------------------------------------
# Core atomization logic
# ----------------------------------------------------------------------
def _flatten_step(step: Dict[str, Any], prefix: str, task_map: Dict[str, AtomicTask]) -> str:
    """
    Convert a single step description into an AtomicTask.
    Returns the created task ID.
    """
    # Expected step format:
    # {
    #   "name": "download_dataset",
    #   "action": "fetch_data",
    #   "params": {"url": "..."},
    #   "depends_on": ["previous_step_name", ...]   # optional, names relative to plan
    # }
    name = step["name"]
    task_id = f"{prefix}.{name}" if prefix else name
    action = step["action"]
    params = step.get("params", {})

    task = AtomicTask(task_id, action, params)

    # Resolve dependencies expressed as step names (relative to same prefix)
    for dep_name in step.get("depends_on", []):
        dep_id = f"{prefix}.{dep_name}" if prefix else dep_name
        task.depends_on.add(dep_id)

    task_map[task_id] = task
    return task_id


def _process_subplan(subplan: List[Dict[str, Any]], prefix: str, task_map: Dict[str, AtomicTask]) -> List[str]:
    """
    Recursively process a list of steps/sub‑plans.
    Returns a list of task IDs generated from this sub‑plan.
    """
    generated_ids: List[str] = []
    for step in subplan:
        # Nested sub‑plan handling – a step may contain a "subplan" key
        if "subplan" in step:
            nested_prefix = f"{prefix}.{step['name']}" if prefix else step["name"]
            # First create a placeholder task for the container if needed
            container_id = _flatten_step(step, prefix, task_map)
            # Process nested steps
            child_ids = _process_subplan(step["subplan"], nested_prefix, task_map)
            # The container depends on all its children (or vice‑versa depending on semantics)
            # Here we treat the container as a logical grouping; children must finish before
            # the container can be considered complete.
            task_map[container_id].depends_on.update(child_ids)
            generated_ids.append(container_id)
        else:
            task_id = _flatten_step(step, prefix, task_map)
            generated_ids.append(task_id)
    return generated_ids


def atomize_plan(plan: Dict[str, Any]) -> Tuple[List[AtomicTask], Dict[str, List[str]]]:
    """
    Convert a high‑level feature plan into atomic tasks and a dependency graph.

    Parameters
    ----------
    plan : dict
        Expected top‑level structure:
        {
            "features": [
                {"name": "...", "action": "...", "params": {...}, "depends_on": [...]},
                {"name": "...", "subplan": [ ... ]},
                ...
            ]
        }

    Returns
    -------
    tasks : List[AtomicTask]
        All atomic tasks (no duplicates).
    graph : Dict[str, List[str]]
        Mapping from task ID -> list of downstream task IDs (i.e., edges).
    """
    if not isinstance(plan, dict) or "features" not in plan:
        raise ValueError("Plan must be a dict containing a top‑level 'features' list.")

    task_map: Dict[str, AtomicTask] = {}
    _process_subplan(plan["features"], prefix="", task_map=task_map)

    # Build forward adjacency list (graph) from depends_on relations
    graph: Dict[str, List[str]] = defaultdict(list)
    for task in task_map.values():
        for dep in task.depends_on:
            graph[dep].append(task.id)

    # Ensure every task appears in the graph even if it has no outgoing edges
    for task_id in task_map:
        graph.setdefault(task_id, [])

    tasks = list(task_map.values())
    return tasks, dict(graph)


# ----------------------------------------------------------------------
# Parallelism groups calculation
# ----------------------------------------------------------------------
def compute_parallelism_groups(tasks: List[AtomicTask]) -> List[Set[str]]:
    """
    Determine sets of tasks that can be executed concurrently.

    The algorithm performs a topological sort and groups tasks by their
    "level" in the DAG: all tasks whose dependencies are satisfied at the same
    iteration belong to the same group.

    Returns
    -------
    groups : List[Set[str]]
        Ordered list where each set contains task IDs runnable in parallel.
    """
    # Build in-degree map
    indegree: Dict[str, int] = {t.id: 0 for t in tasks}
    adjacency: Dict[str, List[str]] = defaultdict(list)
    for t in tasks:
        for dep in t.depends_on:
            indegree[t.id] += 1
            adjacency[dep].append(t.id)

    # Kahn's algorithm – collect zero‑indegree nodes per level
    ready = deque([tid for tid, deg in indegree.items() if deg == 0])
    groups: List[Set[str]] = []

    while ready:
        current_level: Set[str] = set()
        # Process all nodes currently ready (they belong to the same parallel group)
        for _ in range(len(ready)):
            node = ready.popleft()
            current_level.add(node)
            for succ in adjacency.get(node, []):
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    ready.append(succ)
        groups.append(current_level)

    # Detect cycles (any node left with indegree > 0)
    if any(deg > 0 for deg in indegree.values()):
        raise RuntimeError("Cyclic dependency detected in atomic task graph.")

    return groups


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def dump_graph(tasks: List[AtomicTask], graph: Dict[str, List[str]], path: str) -> None:
    """
    Serialize tasks and dependency graph to a JSON file.

    The output structure:
    {
        "tasks": [{task dict}, ...],
        "dependency_graph": {"task_id": ["downstream_id", ...], ...},
        "parallelism_groups": [["task_id", ...], ...]   # optional, calculated on‑the‑fly
    }
    """
    parallel_groups = compute_parallelism_groups(tasks)
    serialisable = {
        "tasks": [t.to_dict() for t in tasks],
        "dependency_graph": graph,
        "parallelism_groups": [list(g) for g in parallel_groups],
    }
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(serialisable, fp, indent=2, sort_keys=True)


# ----------------------------------------------------------------------
# Simple CLI for manual testing (optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys
    import yaml  # Assuming PyYAML is available in the environment

    parser = argparse.ArgumentParser(description="Atomize a feature plan.")
    parser.add_argument("plan_path", help="Path to a YAML or JSON plan file.")
    parser.add_argument(
        "-o",
        "--output",
        default="atomized_graph.json",
        help="Destination JSON file for the graph.",
    )
    args = parser.parse_args()

    # Load plan (YAML preferred, fallback to JSON)
    try:
        with open(args.plan_path, "r", encoding="utf-8") as f:
            if args.plan_path.lower().endswith((".yaml", ".yml")):
                plan_data = yaml.safe_load(f)
            else:
                plan_data = json.load(f)
    except Exception as exc:
        sys.stderr.write(f"Failed to load plan: {exc}\\n")
        sys.exit(1)

    try:
        tasks, dep_graph = atomize_plan(plan_data)
        dump_graph(tasks, dep_graph, args.output)
        print(f"Atomization complete. Graph written to {args.output}")
    except Exception as exc:
        sys.stderr.write(f"Atomization error: {exc}\\n")
        sys.exit(1)