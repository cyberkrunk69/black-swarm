"""
feature_breakdown.py
--------------------

Utility for decomposing a high‑level task into independent features/components,
assigning each to a ``FeaturePlanner`` and exposing parallelism hints.
Integrates a ``UserProxy`` checkpoint to allow resumption after manual
intervention or external verification.

Usage
-----
>>> from feature_breakdown import FeatureBreakdown
>>> fb = FeatureBreakdown(task_description="...") 
>>> fb.add_feature(name="Data Ingestion", deps=[])
>>> fb.add_feature(name="Model Training", deps=["Data Ingestion"])
>>> fb.add_feature(name="Reporting", deps=["Model Training"])
>>> plan = fb.plan()
>>> plan.run_parallel_groups()   # returns list of groups that can run concurrently
>>> fb.checkpoint()              # persists state via UserProxy
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Iterable
import json
import os
import threading

# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class Feature:
    """A single unit of work."""
    name: str
    description: str = ""
    deps: List[str] = field(default_factory=list)  # names of features this one depends on

    def __hash__(self) -> int:
        return hash(self.name)


class FeaturePlanner:
    """
    Holds a collection of Features and provides utilities to reason about
    dependency ordering and parallel execution groups.
    """

    def __init__(self) -> None:
        self._features: Dict[str, Feature] = {}

    # -----------------------------------------------------------------------
    # Feature management
    # -----------------------------------------------------------------------
    def add_feature(self, feature: Feature) -> None:
        if feature.name in self._features:
            raise ValueError(f"Feature '{feature.name}' already exists.")
        self._features[feature.name] = feature

    def get_feature(self, name: str) -> Feature:
        return self._features[name]

    def all_features(self) -> List[Feature]:
        return list(self._features.values())

    # -----------------------------------------------------------------------
    # Dependency analysis
    # -----------------------------------------------------------------------
    def _build_adjacent(self) -> Dict[str, Set[str]]:
        """Return adjacency list where edge A -> B means A must finish before B."""
        adj: Dict[str, Set[str]] = {name: set() for name in self._features}
        for f in self._features.values():
            for dep in f.deps:
                if dep not in self._features:
                    raise ValueError(f"Dependency '{dep}' of feature '{f.name}' not defined.")
                adj[dep].add(f.name)
        return adj

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm – returns a list of feature names in execution order."""
        adj = self._build_adjacent()
        indegree: Dict[str, int] = {name: 0 for name in self._features}
        for src, targets in adj.items():
            for tgt in targets:
                indegree[tgt] += 1

        # start with nodes that have no incoming edges
        queue: List[str] = [n for n, d in indegree.items() if d == 0]
        order: List[str] = []

        while queue:
            node = queue.pop()
            order.append(node)
            for neighbor in adj[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._features):
            raise RuntimeError("Circular dependency detected among features.")
        return order

    # -----------------------------------------------------------------------
    # Parallelism suggestion
    # -----------------------------------------------------------------------
    def suggest_parallel_groups(self) -> List[Set[str]]:
        """
        Returns a list where each entry is a set of feature names that can be
        executed concurrently. The list respects dependency ordering:
        earlier groups must finish before later groups start.
        """
        # Compute levels via BFS over dependency graph
        adj = self._build_adjacent()
        indegree: Dict[str, int] = {name: 0 for name in self._features}
        for src, targets in adj.items():
            for tgt in targets:
                indegree[tgt] += 1

        # Level assignment
        level_map: Dict[str, int] = {}
        current_level = 0
        ready = {n for n, d in indegree.items() if d == 0}
        while ready:
            next_ready: Set[str] = set()
            for node in ready:
                level_map[node] = current_level
                for neighbor in adj[node]:
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        next_ready.add(neighbor)
            current_level += 1
            ready = next_ready

        # Group by level
        max_level = max(level_map.values(), default=-1)
        groups: List[Set[str]] = [set() for _ in range(max_level + 1)]
        for name, lvl in level_map.items():
            groups[lvl].add(name)
        return groups

    # -----------------------------------------------------------------------
    # Execution helper (stub)
    # -----------------------------------------------------------------------
    def run_parallel_groups(self) -> List[Tuple[int, List[threading.Thread]]]:
        """
        Executes each parallel group in its own thread pool (simple stub).
        Returns a list of tuples (group_index, list_of_threads) for inspection.
        """
        groups = self.suggest_parallel_groups()
        results: List[Tuple[int, List[threading.Thread]]] = []

        for idx, group in enumerate(groups):
            threads: List[threading.Thread] = []
            for feature_name in group:
                t = threading.Thread(target=self._execute_feature_stub, args=(feature_name,))
                t.start()
                threads.append(t)
            # Wait for this group to finish before moving to the next
            for t in threads:
                t.join()
            results.append((idx, threads))
        return results

    @staticmethod
    def _execute_feature_stub(name: str) -> None:
        """Placeholder for real execution logic."""
        print(f"[FeaturePlanner] Executing feature: {name}")

# ---------------------------------------------------------------------------
# User Proxy checkpoint integration
# ---------------------------------------------------------------------------

class UserProxy:
    """
    Simple checkpoint manager that persists the FeaturePlanner state to a JSON
    file. In a real system this would be replaced by a more robust user‑proxy
    service.
    """

    def __init__(self, checkpoint_dir: str = ".") -> None:
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)

    def _path(self, name: str) -> str:
        return os.path.join(self.checkpoint_dir, f"{name}.json")

    def save(self, name: str, data: dict) -> None:
        with open(self._path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, name: str) -> dict | None:
        try:
            with open(self._path(name), "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None

# ---------------------------------------------------------------------------
# High‑level orchestrator
# ---------------------------------------------------------------------------

class FeatureBreakdown:
    """
    High‑level façade used by experiment scripts. Handles feature registration,
    planning, parallel‑group suggestion and checkpoint persistence.
    """

    def __init__(self, task_description: str = "", checkpoint_name: str = "feature_breakdown"):
        self.task_description = task_description
        self.planner = FeaturePlanner()
        self.checkpoint_name = checkpoint_name
        self.user_proxy = UserProxy(checkpoint_dir="checkpoints")

        # Attempt to restore previous state
        saved = self.user_proxy.load(self.checkpoint_name)
        if saved:
            self._restore_state(saved)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def add_feature(self, name: str, description: str = "", deps: Iterable[str] = ()) -> None:
        feature = Feature(name=name, description=description, deps=list(deps))
        self.planner.add_feature(feature)

    def plan(self) -> FeaturePlanner:
        """Return the underlying planner after validating the graph."""
        # Validation performed lazily via topological sort
        self.planner._topological_sort()
        return self.planner

    def suggest_parallel_groups(self) -> List[Set[str]]:
        return self.planner.suggest_parallel_groups()

    def checkpoint(self) -> None:
        """Persist current feature set to the UserProxy."""
        data = {
            "task_description": self.task_description,
            "features": [
                {
                    "name": f.name,
                    "description": f.description,
                    "deps": f.deps,
                }
                for f in self.planner.all_features()
            ],
        }
        self.user_proxy.save(self.checkpoint_name, data)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------
    def _restore_state(self, data: dict) -> None:
        self.task_description = data.get("task_description", "")
        for fdata in data.get("features", []):
            self.add_feature(
                name=fdata["name"],
                description=fdata.get("description", ""),
                deps=fdata.get("deps", []),
            )

# ---------------------------------------------------------------------------
# Example entry‑point (executed only when run as script)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simple demo showing how the module can be used.
    fb = FeatureBreakdown(task_description="Demo experiment")
    fb.add_feature("Data Ingestion")
    fb.add_feature("Preprocess", deps=["Data Ingestion"])
    fb.add_feature("Model Training", deps=["Preprocess"])
    fb.add_feature("Evaluation", deps=["Model Training"])
    fb.add_feature("Reporting", deps=["Evaluation"])

    planner = fb.plan()
    groups = fb.suggest_parallel_groups()
    print("Parallel groups suggestion:")
    for idx, grp in enumerate(groups):
        print(f"  Group {idx}: {sorted(grp)}")

    # Run stub execution to illustrate parallelism handling
    planner.run_parallel_groups()

    # Persist state
    fb.checkpoint()
    print("Checkpoint saved.")