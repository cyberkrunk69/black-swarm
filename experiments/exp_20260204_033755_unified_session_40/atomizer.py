#!/usr/bin/env python3
"""
atomizer.py

Utility to convert a high‑level feature plan into a minimal set of atomic
tasks, generate a dependency graph, and compute parallelism groups
(i.e., which tasks can be executed concurrently).

The implementation follows the *Atomizer Node* description in
SWARM_ARCHITECTURE_V2.md:
*   Each feature is broken down into the smallest executable unit.
*   Dependencies between features become directed edges in a DAG.
*   Parallelism groups are derived from a topological layering of the DAG.

Usage
-----
    python -m atomizer <plan.json> [--out <out.json>]

    * ``plan.json`` – JSON array of feature specifications.
    * ``out.json``  – Optional path where the resulting JSON will be saved.
      If omitted the result is printed to stdout.

Input format (plan.json)
------------------------
[
    {
        "id": "feature_A",
        "action": "compile",
        "params": {...},
        "depends_on": ["feature_B", "feature_C"]
    },
    ...
]

Output format
-------------
{
    "tasks": [
        {
            "task_id": "<unique atomic id>",
            "feature_id": "<original feature id>",
            "action": "...",
            "params": {...}
        },
        ...
    ],
    "dependency_graph": {
        "<task_id>": ["<dependent_task_id>", ...],
        ...
    },
    "parallelism_groups": [
        ["task_id_1", "task_id_2"],   # group 0 – can run concurrently
        ["task_id_3"],                # group 1 – runs after group 0
        ...
    ]
}
"""

import json
import sys
import argparse
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple


def _validate_plan(plan: List[dict]) -> None:
    """Basic validation of the feature plan."""
    ids = set()
    for feature in plan:
        if "id" not in feature:
            raise ValueError("Every feature must contain an 'id' field.")
        fid = feature["id"]
        if fid in ids:
            raise ValueError(f"Duplicate feature id detected: {fid}")
        ids.add(fid)

    for feature in plan:
        for dep in feature.get("depends_on", []):
            if dep not in ids:
                raise ValueError(f"Feature '{feature['id']}' depends on unknown id '{dep}'.")


def _topological_sort(
    graph: Dict[str, Set[str]]
) -> Tuple[List[str], List[List[str]]]:
    """
    Perform Kahn's algorithm to obtain a topological ordering and
    derive parallelism groups (layers).

    Returns
    -------
    order : List[str]
        Linear topological order of task ids.
    groups : List[List[str]]
        Each inner list contains tasks that can be executed in parallel.
    """
    # Compute in‑degree for each node
    indegree = {node: 0 for node in graph}
    for deps in graph.values():
        for dep in deps:
            indegree[dep] += 1

    # Queue of nodes with zero indegree
    zero_q = deque([n for n, d in indegree.items() if d == 0])

    order: List[str] = []
    groups: List[List[str]] = []

    while zero_q:
        # All nodes currently in zero_q belong to the same parallel group
        current_group = list(zero_q)
        groups.append(current_group)

        for _ in range(len(zero_q)):
            node = zero_q.popleft()
            order.append(node)
            for succ in graph[node]:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    zero_q.append(succ)

    if len(order) != len(graph):
        raise RuntimeError("Cyclic dependency detected in the feature plan.")
    return order, groups


def atomize(feature_plan: List[dict]) -> dict:
    """
    Convert a feature plan into atomic tasks, a dependency graph, and
    parallelism groups.

    Parameters
    ----------
    feature_plan : List[dict]
        List of feature specifications as described in the module docstring.

    Returns
    -------
    dict
        {
            "tasks": [...],
            "dependency_graph": {...},
            "parallelism_groups": [...]
        }
    """
    _validate_plan(feature_plan)

    # ------------------------------------------------------------------
    # 1. Create atomic tasks.
    #    For this generic implementation each feature becomes a single
    #    atomic task.  In a real system the feature could be further split
    #    into multiple subtasks; the logic would be placed here.
    # ------------------------------------------------------------------
    tasks: List[dict] = []
    task_id_map: Dict[str, str] = {}   # feature_id -> task_id

    for idx, feature in enumerate(feature_plan):
        task_id = f"task_{idx}"
        task = {
            "task_id": task_id,
            "feature_id": feature["id"],
            "action": feature.get("action", "noop"),
            "params": feature.get("params", {})
        }
        tasks.append(task)
        task_id_map[feature["id"]] = task_id

    # ------------------------------------------------------------------
    # 2. Build the dependency graph (DAG) where edges point from a task
    #    to the tasks that depend on it.
    # ------------------------------------------------------------------
    dep_graph: Dict[str, Set[str]] = defaultdict(set)
    # Ensure every task appears in the graph even if it has no outgoing edges
    for task in tasks:
        dep_graph[task["task_id"]] = set()

    for feature in feature_plan:
        src_task = task_id_map[feature["id"]]
        for dep_feat in feature.get("depends_on", []):
            dst_task = task_id_map[dep_feat]
            # Edge: dst_task -> src_task (dst must finish before src)
            dep_graph[dst_task].add(src_task)

    # ------------------------------------------------------------------
    # 3. Topological sort + parallelism groups.
    # ------------------------------------------------------------------
    _, parallelism_groups = _topological_sort(dep_graph)

    # Convert sets to sorted lists for JSON friendliness
    dep_graph_json = {k: sorted(list(v)) for k, v in dep_graph.items()}

    result = {
        "tasks": tasks,
        "dependency_graph": dep_graph_json,
        "parallelism_groups": parallelism_groups
    }
    return result


def _load_plan(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Feature plan JSON must be a list of feature objects.")
    return data


def _save_output(output: dict, path: str = None) -> None:
    serialized = json.dumps(output, indent=2, sort_keys=True)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(serialized + "\n")
    else:
        sys.stdout.write(serialized + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Atomize a feature plan into minimal parallelizable tasks."
    )
    parser.add_argument(
        "plan",
        help="Path to the JSON file containing the feature plan."
    )
    parser.add_argument(
        "--out",
        help="Optional output file for the generated JSON. Defaults to stdout."
    )
    args = parser.parse_args()

    try:
        plan = _load_plan(args.plan)
        result = atomize(plan)
        _save_output(result, args.out)
    except Exception as exc:
        sys.stderr.write(f"Error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()