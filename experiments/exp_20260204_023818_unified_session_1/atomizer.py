"""
atomizer.py

Converts high‑level feature plans into a minimal set of atomic tasks,
produces a dependency graph, and determines parallelism groups.

The implementation follows the “Atomizer Node” description in
SWARM_ARCHITECTURE_V2.md.

Typical usage:

    from atomizer import Atomizer

    feature_plan = [
        {"id": "A", "action": "extract", "inputs": []},
        {"id": "B", "action": "transform", "inputs": ["A"]},
        {"id": "C", "action": "load", "inputs": ["B"]},
        {"id": "D", "action": "audit", "inputs": ["A"]},
    ]

    atomizer = Atomizer(feature_plan)
    tasks, dep_graph, parallel_groups = atomizer.run()

    # tasks   -> list of atomic task dicts
    # dep_graph -> {"A": ["B","D"], ...}
    # parallel_groups -> list of lists, each inner list may be executed in parallel
"""

import json
from collections import defaultdict, deque
from typing import List, Dict, Set, Tuple, Any


class AtomizerError(Exception):
    """Custom exception for atomizer failures."""
    pass


class Atomizer:
    """
    Core class that transforms a feature plan into atomic tasks,
    builds a dependency graph and calculates parallelism groups.
    """

    def __init__(self, feature_plan: List[Dict[str, Any]]):
        """
        :param feature_plan: List of dicts where each dict describes a high‑level
                             feature step.

        Expected dict schema:
            {
                "id": <unique string identifier>,
                "action": <string describing the operation>,
                "inputs": <list of ids this step depends on>,
                "params": <optional dict of extra parameters>
            }
        """
        self.raw_plan = feature_plan
        self._validate_plan()
        self.tasks: List[Dict[str, Any]] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    # --------------------------------------------------------------------- #
    # Validation helpers
    # --------------------------------------------------------------------- #
    def _validate_plan(self) -> None:
        """Ensures the feature plan is well‑formed and acyclic."""
        seen_ids: Set[str] = set()
        for step in self.raw_plan:
            if "id" not in step or "action" not in step or "inputs" not in step:
                raise AtomizerError(f"Step missing required keys: {step}")
            if step["id"] in seen_ids:
                raise AtomizerError(f"Duplicate step id detected: {step['id']}")
            seen_ids.add(step["id"])

        # Detect cycles using Kahn's algorithm
        indegree: Dict[str, int] = {step["id"]: 0 for step in self.raw_plan}
        adjacency: Dict[str, List[str]] = defaultdict(list)

        for step in self.raw_plan:
            for dep in step["inputs"]:
                if dep not in indegree:
                    raise AtomizerError(f"Undefined dependency '{dep}' in step {step['id']}")
                adjacency[dep].append(step["id"])
                indegree[step["id"]] += 1

        q = deque([node for node, deg in indegree.items() if deg == 0])
        visited = 0
        while q:
            node = q.popleft()
            visited += 1
            for nxt in adjacency[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    q.append(nxt)

        if visited != len(self.raw_plan):
            raise AtomizerError("Cyclic dependency detected in feature plan")

    # --------------------------------------------------------------------- #
    # Core transformation
    # --------------------------------------------------------------------- #
    def _create_atomic_tasks(self) -> None:
        """
        Translates each high‑level step into an atomic task dict.
        The atomic task keeps the original id, action, params and expands
        inputs to a list of predecessor ids.
        """
        for step in self.raw_plan:
            atomic = {
                "task_id": step["id"],
                "action": step["action"],
                "params": step.get("params", {}),
                "depends_on": list(step["inputs"]),  # copy to avoid mutation
            }
            self.tasks.append(atomic)

    def _build_dependency_graph(self) -> None:
        """
        Populates self.dependency_graph (forward) and self.reverse_graph (backward).
        """
        for task in self.tasks:
            tid = task["task_id"]
            for dep in task["depends_on"]:
                self.dependency_graph[dep].add(tid)   # dep -> tid
                self.reverse_graph[tid].add(dep)      # tid -> dep

        # Ensure every task appears as a key in both dicts
        for task in self.tasks:
            tid = task["task_id"]
            self.dependency_graph.setdefault(tid, set())
            self.reverse_graph.setdefault(tid, set())

    # --------------------------------------------------------------------- #
    # Parallelism groups calculation
    # --------------------------------------------------------------------- #
    def _calculate_parallel_groups(self) -> List[List[str]]:
        """
        Returns a list of groups where each inner list contains task_ids that
        can be executed in parallel. The algorithm is a level‑order topological
        sort (Kahn's algorithm) where each level corresponds to a parallel group.
        """
        indegree: Dict[str, int] = {tid: len(parents) for tid, parents in self.reverse_graph.items()}
        ready = [tid for tid, deg in indegree.items() if deg == 0]
        groups: List[List[str]] = []

        while ready:
            groups.append(sorted(ready))  # deterministic order
            next_ready: List[str] = []
            for node in ready:
                for succ in self.dependency_graph[node]:
                    indegree[succ] -= 1
                    if indegree[succ] == 0:
                        next_ready.append(succ)
            ready = next_ready

        # Sanity check: all nodes must be scheduled
        total_scheduled = sum(len(g) for g in groups)
        if total_scheduled != len(self.tasks):
            raise AtomizerError("Failed to schedule all tasks into parallel groups")
        return groups

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]], List[List[str]]]:
        """
        Executes the full atomization pipeline.

        :return: (tasks, dependency_graph_json_compatible, parallel_groups)
        """
        self._create_atomic_tasks()
        self._build_dependency_graph()
        parallel_groups = self._calculate_parallel_groups()

        # Convert sets to sorted lists for JSON friendliness
        dep_graph_json = {
            key: sorted(list(val)) for key, val in self.dependency_graph.items()
        }

        return self.tasks, dep_graph_json, parallel_groups

    # --------------------------------------------------------------------- #
    # Convenience helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def dump_to_json(tasks: List[Dict[str, Any]],
                     dep_graph: Dict[str, List[str]],
                     parallel_groups: List[List[str]],
                     filepath: str) -> None:
        """
        Persists the atomizer output to a single JSON file.

        Structure:
        {
            "tasks": [...],
            "dependency_graph": {...},
            "parallel_groups": [...]
        }
        """
        data = {
            "tasks": tasks,
            "dependency_graph": dep_graph,
            "parallel_groups": parallel_groups,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)

# ------------------------------------------------------------------------- #
# Example execution (executed when run as a script)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple demo plan – in real usage the plan would be loaded from a
    # higher‑level orchestration component.
    demo_plan = [
        {"id": "extract_user", "action": "extract", "inputs": []},
        {"id": "extract_orders", "action": "extract", "inputs": []},
        {"id": "join_user_orders", "action": "join", "inputs": ["extract_user", "extract_orders"]},
        {"id": "calc_metrics", "action": "aggregate", "inputs": ["join_user_orders"]},
        {"id": "store_metrics", "action": "load", "inputs": ["calc_metrics"]},
    ]

    atomizer = Atomizer(demo_plan)
    tasks, dep_graph, groups = atomizer.run()

    print("Atomic Tasks:")
    print(json.dumps(tasks, indent=2))
    print("\nDependency Graph:")
    print(json.dumps(dep_graph, indent=2))
    print("\nParallelism Groups (execution levels):")
    print(json.dumps(groups, indent=2))

    # Optionally persist
    Atomizer.dump_to_json(tasks, dep_graph, groups, "atomizer_output.json")