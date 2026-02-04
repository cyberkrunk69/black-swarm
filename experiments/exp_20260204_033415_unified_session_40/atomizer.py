"""
atomizer.py
~~~~~~~~~~~

Converts a high‑level feature‑plan description into a minimal set of
atomic, parallelizable tasks together with a dependency graph.
The output consists of two JSON files:

* ``tasks.json`` – a flat list of atomic tasks.
* ``graph.json`` – a representation of the directed acyclic graph (DAG)
  that captures task dependencies and the calculated parallelism groups.

The implementation follows the *Atomizer Node* description in
``SWARM_ARCHITECTURE_V2.md``.
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Any


# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #
class AtomicTask:
    """Simple container for an atomic task."""

    def __init__(self, task_id: str, payload: Dict[str, Any]):
        self.id = task_id
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "payload": self.payload}


# --------------------------------------------------------------------------- #
# Core atomizer logic
# --------------------------------------------------------------------------- #
def _build_dependency_graph(
    raw_tasks: List[Dict[str, Any]]
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    Build forward and reverse adjacency lists.

    Returns:
        forward:  task_id -> set(dependent_task_ids)
        reverse:  task_id -> set(prerequisite_task_ids)
    """
    forward: Dict[str, Set[str]] = defaultdict(set)
    reverse: Dict[str, Set[str]] = defaultdict(set)

    for task in raw_tasks:
        task_id = task["id"]
        deps = set(task.get("depends_on", []))
        reverse[task_id] = deps
        for dep in deps:
            forward[dep].add(task_id)

    # Ensure every task appears in both dicts
    for t in [t["id"] for t in raw_tasks]:
        forward.setdefault(t, set())
        reverse.setdefault(t, set())

    return forward, reverse


def _topological_sort(
    forward: Dict[str, Set[str]], reverse: Dict[str, Set[str]]
) -> List[str]:
    """
    Perform Kahn's algorithm to obtain a topological ordering.
    Raises a ValueError if a cycle is detected.
    """
    in_degree: Dict[str, int] = {node: len(parents) for node, parents in reverse.items()}
    zero_in = deque([node for node, deg in in_degree.items() if deg == 0])

    order: List[str] = []
    while zero_in:
        node = zero_in.popleft()
        order.append(node)
        for succ in forward[node]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                zero_in.append(succ)

    if len(order) != len(in_degree):
        raise ValueError("Cyclic dependency detected in feature plan.")
    return order


def _calculate_parallelism_groups(
    order: List[str], reverse: Dict[str, Set[str]]
) -> List[List[str]]:
    """
    Group tasks into levels such that tasks in the same level have no
    mutual dependencies and can be executed in parallel.

    The algorithm walks the topological order and assigns each node to the
    smallest possible level where all its prerequisites are in earlier levels.
    """
    level_of: Dict[str, int] = {}
    max_level = 0

    for node in order:
        if not reverse[node]:
            lvl = 0
        else:
            lvl = 1 + max(level_of[parent] for parent in reverse[node])
        level_of[node] = lvl
        max_level = max(max_level, lvl)

    groups: List[List[str]] = [[] for _ in range(max_level + 1)]
    for node, lvl in level_of.items():
        groups[lvl].append(node)

    # Remove empty groups (should not happen) and return
    return [g for g in groups if g]


def atomize(feature_plan: Dict[str, Any]) -> Tuple[List[AtomicTask], Dict[str, Any]]:
    """
    Main entry point – transform a feature plan into atomic tasks and a
    dependency graph.

    The expected ``feature_plan`` format (as described in the architecture
    doc) is:

    {
        "tasks": [
            {
                "id": "unique_task_id",
                "payload": {...},          # arbitrary data required by the worker
                "depends_on": ["id1", …]   # optional list of prerequisite task ids
            },
            …
        ]
    }

    Returns:
        tasks: List of :class:`AtomicTask` objects (already minimal/atomic).
        graph: Dict containing:
            - "edges": List[Tuple[str, str]]   (src, dst)
            - "parallelism_groups": List[List[str]]
    """
    raw_tasks = feature_plan.get("tasks", [])
    if not raw_tasks:
        raise ValueError("Feature plan must contain a non‑empty 'tasks' list.")

    forward, reverse = _build_dependency_graph(raw_tasks)
    order = _topological_sort(forward, reverse)
    parallel_groups = _calculate_parallelism_groups(order, reverse)

    # Build atomic task objects (the plan is already atomic; we just wrap)
    atomic_tasks = [AtomicTask(t["id"], t.get("payload", {})) for t in raw_tasks]

    # Serialize edges for the graph output
    edges = [(src, dst) for src, succs in forward.items() for dst in succs]

    graph = {
        "edges": edges,
        "parallelism_groups": parallel_groups,
        "topological_order": order,
    }

    return atomic_tasks, graph


# --------------------------------------------------------------------------- #
# CLI utilities
# --------------------------------------------------------------------------- #
def _write_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)


def main(argv: List[str] | None = None) -> int:
    """
    CLI usage:

        python atomizer.py <feature_plan.json> <output_dir>

    The script writes two files into ``output_dir``:
        - tasks.json
        - graph.json
    """
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 2:
        sys.stderr.write(
            "Usage: python atomizer.py <feature_plan.json> <output_dir>\n"
        )
        return 1

    plan_path, out_dir = argv
    if not os.path.isfile(plan_path):
        sys.stderr.write(f"Feature plan not found: {plan_path}\n")
        return 1

    os.makedirs(out_dir, exist_ok=True)

    with open(plan_path, "r", encoding="utf-8") as fp:
        feature_plan = json.load(fp)

    try:
        tasks, graph = atomize(feature_plan)
    except Exception as exc:
        sys.stderr.write(f"Atomization failed: {exc}\n")
        return 1

    # Write outputs
    _write_json([t.to_dict() for t in tasks], os.path.join(out_dir, "tasks.json"))
    _write_json(graph, os.path.join(out_dir, "graph.json"))

    print(f"Atomization complete. Produced {len(tasks)} tasks.")
    print(f"Dependency graph written to {os.path.join(out_dir, 'graph.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())