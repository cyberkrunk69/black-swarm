"""
feature_breakdown.py

Utility to split a high‑level project description into independent features,
assign each feature to a FeaturePlanner, and suggest which features can be
executed in parallel.  It also integrates a simple User Proxy checkpoint
mechanism so that long‑running planning sessions can be resumed safely.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Callable, Any
import json
import os
import hashlib
import threading

# ----------------------------------------------------------------------
# Core data structures
# ----------------------------------------------------------------------


@dataclass
class Feature:
    """A single, independently implementable piece of work."""
    name: str
    description: str
    dependencies: Set[str] = field(default_factory=set)

    def __hash__(self) -> int:
        # Hash based on name – names must be unique within a project
        return hash(self.name)


@dataclass
class FeaturePlanner:
    """Container for planning a feature.  In a real system this would be
    more elaborate; here we just keep a reference to the Feature and a
    placeholder for planning state."""
    feature: Feature
    state: Dict[str, Any] = field(default_factory=dict)

    def plan(self) -> None:
        """Placeholder planning routine."""
        # In a real implementation this would generate tasks, estimate effort,
        # assign owners, etc.  We just record a timestamp.
        import time
        self.state["planned_at"] = time.time()
        self.state["status"] = "planned"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature": {
                "name": self.feature.name,
                "description": self.feature.description,
                "dependencies": list(self.feature.dependencies),
            },
            "state": self.state,
        }


# ----------------------------------------------------------------------
# Parallelism suggestion logic
# ----------------------------------------------------------------------


def _build_dependency_graph(features: List[Feature]) -> Dict[str, Set[str]]:
    """Return a mapping from feature name to the set of features that must
    precede it."""
    graph: Dict[str, Set[str]] = {}
    for f in features:
        graph[f.name] = set(f.dependencies)
    return graph


def _topological_sort(graph: Dict[str, Set[str]]) -> List[Set[str]]:
    """
    Perform a topological sort that groups independent nodes together.
    Returns a list where each element is a set of feature names that can
    run in parallel (no dependencies between them).
    Raises ValueError on cycles.
    """
    # Kahn's algorithm with grouping
    in_degree: Dict[str, int] = {node: len(deps) for node, deps in graph.items()}
    zero_in: Set[str] = {node for node, deg in in_degree.items() if deg == 0}
    result: List[Set[str]] = []

    while zero_in:
        result.append(set(zero_in))
        next_zero: Set[str] = set()
        for node in zero_in:
            # Remove node from graph
            for succ, deps in graph.items():
                if node in deps:
                    deps.remove(node)
                    in_degree[succ] -= 1
                    if in_degree[succ] == 0:
                        next_zero.add(succ)
        zero_in = next_zero

    if any(deps for deps in graph.values()):
        raise ValueError("Cyclic dependency detected among features")
    return result


def suggest_parallelism(features: List[Feature]) -> List[Set[str]]:
    """
    Given a list of Feature objects, return a list of sets.  Each set contains
    feature names that can be executed concurrently.
    """
    graph = _build_dependency_graph(features)
    return _topological_sort(graph)


# ----------------------------------------------------------------------
# User Proxy checkpoint integration
# ----------------------------------------------------------------------


class UserProxyCheckpoint:
    """
    Simple checkpoint manager that serialises the planning state to disk.
    The checkpoint file is named after a hash of the experiment directory,
    guaranteeing isolation between experiments.
    """

    def __init__(self, experiment_root: str):
        self.experiment_root = os.path.abspath(experiment_root)
        self.checkpoint_path = os.path.join(
            self.experiment_root,
            f".checkpoint_{self._hash_path()}.json",
        )
        self.lock = threading.Lock()

    def _hash_path(self) -> str:
        return hashlib.sha256(self.experiment_root.encode()).hexdigest()[:12]

    def save(self, planners: List[FeaturePlanner]) -> None:
        """Serialise the list of planners to the checkpoint file."""
        data = [planner.to_dict() for planner in planners]
        with self.lock, open(self.checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> List[FeaturePlanner]:
        """Load planners from the checkpoint file. Returns an empty list if
        no checkpoint exists."""
        if not os.path.exists(self.checkpoint_path):
            return []
        with self.lock, open(self.checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        planners: List[FeaturePlanner] = []
        for entry in data:
            feat_data = entry["feature"]
            feature = Feature(
                name=feat_data["name"],
                description=feat_data["description"],
                dependencies=set(feat_data["dependencies"]),
            )
            planner = FeaturePlanner(feature=feature, state=entry.get("state", {}))
            planners.append(planner)
        return planners


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def breakdown_into_features(
    raw_descriptions: List[Tuple[str, str, List[str]]],
) -> List[Feature]:
    """
    Convert a raw list of (name, description, dependencies) into Feature objects.
    Dependencies are supplied as a list of feature names.
    """
    return [
        Feature(name=name, description=desc, dependencies=set(deps))
        for name, desc, deps in raw_descriptions
    ]


def plan_features(
    features: List[Feature],
    experiment_root: str,
    resume: bool = False,
) -> Tuple[List[FeaturePlanner], List[Set[str]]]:
    """
    Main entry point.

    * Creates a FeaturePlanner for each feature.
    * Optionally resumes from a checkpoint.
    * Executes the planning step for each planner.
    * Returns the list of planners and a parallelism suggestion.

    Parameters
    ----------
    features: List[Feature]
        The independent features to be planned.
    experiment_root: str
        Path to the experiment directory (used for checkpoint storage).
    resume: bool
        If True, load existing planners from the checkpoint and continue.
    """
    checkpoint = UserProxyCheckpoint(experiment_root)

    if resume:
        planners = checkpoint.load()
        # Ensure we have planners for any newly added features
        existing_names = {p.feature.name for p in planners}
        for f in features:
            if f.name not in existing_names:
                planners.append(FeaturePlanner(feature=f))
    else:
        planners = [FeaturePlanner(feature=f) for f in features]

    # Run planning (could be parallelised later)
    for planner in planners:
        if planner.state.get("status") != "planned":
            planner.plan()

    # Persist checkpoint
    checkpoint.save(planners)

    # Parallelism suggestion
    parallel_groups = suggest_parallelism(features)

    return planners, parallel_groups


# ----------------------------------------------------------------------
# Example usage (executed only when run as a script)
# ----------------------------------------------------------------------


if __name__ == "__main__":
    # Example raw feature definitions
    raw = [
        ("auth", "User authentication and session handling", []),
        ("api", "REST API endpoints", ["auth"]),
        ("frontend", "Web UI built with React", ["api"]),
        ("billing", "Payment processing integration", ["auth"]),
        ("notifications", "Email & push notifications", ["api", "billing"]),
    ]

    feats = breakdown_into_features(raw)
    root_dir = os.path.dirname(__file__)  # experiment directory
    planners, parallel = plan_features(feats, root_dir, resume=False)

    print("Feature planners created:")
    for p in planners:
        print(f"- {p.feature.name}: {p.state}")

    print("\nParallel execution groups (order matters):")
    for i, group in enumerate(parallel, 1):
        print(f"Stage {i}: {', '.join(sorted(group))}")