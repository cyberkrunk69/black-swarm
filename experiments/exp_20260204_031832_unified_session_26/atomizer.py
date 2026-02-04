"""
atomizer.py

Converts high‑level feature plans into a minimal set of atomic tasks,
produces a dependency graph, and groups tasks that can be executed in
parallel.

The implementation follows the "Atomizer Node" description in
SWARM_ARCHITECTURE_V2.md.
"""

from __future__ import annotations
import json
import itertools
from collections import defaultdict, deque
from typing import Any, Dict, List, Set, Tuple, Iterable


# ----------------------------------------------------------------------
# Types
# ----------------------------------------------------------------------
FeaturePlan = Dict[str, Any]          # Raw user supplied plan
AtomicTask = Dict[str, Any]           # Normalised atomic task description
TaskID = str
DepGraph = Dict[TaskID, Set[TaskID]]  # adjacency list: task -> set(predecessors)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _hash_task(task: AtomicTask) -> TaskID:
    """
    Produce a deterministic ID for a task.
    Uses JSON‑sorted representation to guarantee reproducibility.
    """
    # Remove any existing ID to avoid circularity
    task_copy = {k: v for k, v in task.items() if k != "id"}
    serialized = json.dumps(task_copy, sort_keys=True, separators=(",", ":"))
    return f"t_{abs(hash(serialized)) % (10 ** 12)}"


def _topological_sort(dep_graph: DepGraph) -> List[TaskID]:
    """
    Return a list of task IDs in topological order.
    Raises ValueError on cycles.
    """
    indegree = {node: 0 for node in dep_graph}
    for succs in dep_graph.values():
        for succ in succs:
            indegree[succ] = indegree.get(succ, 0) + 1

    queue = deque([n for n, d in indegree.items() if d == 0])
    order = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for succ in dep_graph.get(node, []):
            indegree[succ] -= 1
            if indegree[succ] == 0:
                queue.append(succ)

    if len(order) != len(dep_graph):
        raise ValueError("Cyclic dependency detected in task graph.")
    return order


# ----------------------------------------------------------------------
# Core Atomizer
# ----------------------------------------------------------------------
class Atomizer:
    """
    Public API:
        Atomizer(feature_plans).atomize()
    Returns:
        {
            "tasks": [AtomicTask, ...],
            "dependency_graph": {task_id: [predecessor_id, ...], ...},
            "parallelism_groups": [[task_id, ...], ...]   # each inner list can run concurrently
        }
    """

    def __init__(self, feature_plans: Iterable[FeaturePlan]):
        self.raw_plans = list(feature_plans)
        self.tasks: List[AtomicTask] = []
        self.task_index: Dict[TaskID, AtomicTask] = {}
        self.dep_graph: DepGraph = defaultdict(set)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def atomize(self) -> Dict[str, Any]:
        self._expand_plans()
        self._build_dependency_graph()
        parallel_groups = self._calculate_parallelism_groups()
        return {
            "tasks": self.tasks,
            "dependency_graph": {k: list(v) for k, v in self.dep_graph.items()},
            "parallelism_groups": parallel_groups,
        }

    # ------------------------------------------------------------------
    # Step 1 – expand high‑level plans into atomic tasks
    # ------------------------------------------------------------------
    def _expand_plans(self) -> None:
        """
        Walk each feature plan and emit the smallest executable unit.
        A plan is expected to be a dict with at least:
            - "feature": name of the feature
            - "actions": list of actions (create, update, delete, transform, etc.)
        Each action may reference other features, establishing implicit dependencies.
        """
        for plan in self.raw_plans:
            feature = plan.get("feature")
            actions = plan.get("actions", [])
            for idx, action in enumerate(actions):
                task: AtomicTask = {
                    "feature": feature,
                    "action_type": action.get("type"),
                    "parameters": action.get("params", {}),
                    "source_features": action.get("depends_on", []),  # explicit deps
                    "original_index": idx,
                }
                task_id = _hash_task(task)
                task["id"] = task_id
                self.tasks.append(task)
                self.task_index[task_id] = task

    # ------------------------------------------------------------------
    # Step 2 – construct dependency graph
    # ------------------------------------------------------------------
    def _build_dependency_graph(self) -> None:
        """
        Populate self.dep_graph where edges point from predecessor -> successor.
        Dependencies are derived from:
            1. Explicit `source_features` listed in each action.
            2. Implicit ordering within the same feature (action sequence).
        """
        # Mapping from feature to list of task IDs in their original order
        feature_to_tasks: Dict[str, List[TaskID]] = defaultdict(list)

        for task in self.tasks:
            task_id = task["id"]
            feature = task["feature"]
            feature_to_tasks[feature].append(task_id)

        # 1) Implicit sequential ordering per feature
        for task_ids in feature_to_tasks.values():
            for pred, succ in zip(task_ids, task_ids[1:]):
                self.dep_graph[succ].add(pred)

        # 2) Explicit cross‑feature dependencies
        # Build a quick lookup: feature -> last task that produces it
        # (Assume the last task for a feature is its "producer")
        feature_producer: Dict[str, TaskID] = {}
        for feature, ids in feature_to_tasks.items():
            feature_producer[feature] = ids[-1]

        for task in self.tasks:
            task_id = task["id"]
            for src_feature in task.get("source_features", []):
                producer_id = feature_producer.get(src_feature)
                if producer_id:
                    self.dep_graph[task_id].add(producer_id)

        # Ensure every task appears in the graph even if it has no deps
        for task in self.tasks:
            self.dep_graph.setdefault(task["id"], set())

    # ------------------------------------------------------------------
    # Step 3 – calculate parallelism groups
    # ------------------------------------------------------------------
    def _calculate_parallelism_groups(self) -> List[List[TaskID]]:
        """
        Group tasks that can run concurrently.
        Approach:
            1. Perform a topological sort.
            2. Walk the sorted list, maintaining a set of tasks whose
               predecessors have all been placed in earlier groups.
            3. When the set grows, emit it as the next parallel group.
        """
        order = _topological_sort(self.dep_graph)

        # Map task -> number of unmet predecessors
        unmet: Dict[TaskID, int] = {
            t: len(preds) for t, preds in self.dep_graph.items()
        }

        ready: Set[TaskID] = {t for t, cnt in unmet.items() if cnt == 0}
        groups: List[List[TaskID]] = []

        while ready:
            current_group = list(sorted(ready))  # deterministic ordering
            groups.append(current_group)

            # Consume the group
            next_ready: Set[TaskID] = set()
            for completed in current_group:
                # Remove completed from unmet counts of its successors
                for succ in self._successors(completed):
                    unmet[succ] -= 1
                    if unmet[succ] == 0:
                        next_ready.add(succ)
                # Mark as processed
                unmet.pop(completed, None)
            ready = next_ready

        if unmet:
            # Should never happen because topological sort already validated.
            raise RuntimeError("Unresolved dependencies after grouping.")

        return groups

    def _successors(self, task_id: TaskID) -> Set[TaskID]:
        """Return all tasks that list *task_id* as a predecessor."""
        succs = {t for t, preds in self.dep_graph.items() if task_id in preds}
        return succs


# ----------------------------------------------------------------------
# Convenience CLI (optional but handy for debugging)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys
    import yaml

    parser = argparse.ArgumentParser(description="Atomize feature plans.")
    parser.add_argument(
        "plan_file",
        type=argparse.FileType("r"),
        help="YAML or JSON file containing a list of feature plans.",
    )
    args = parser.parse_args()

    try:
        raw = yaml.safe_load(args.plan_file)
        if not isinstance(raw, list):
            raise ValueError("Root document must be a list of feature plans.")
    except Exception as exc:
        sys.stderr.write(f"Failed to parse input file: {exc}\n")
        sys.exit(1)

    atomizer = Atomizer(raw)
    result = atomizer.atomize()
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")