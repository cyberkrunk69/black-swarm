\"\"\"feature_breakdown.py
Utility to split a large workload into independent features/components,
assign each to a FeaturePlanner, and suggest parallel execution groups.
Integrates with the User Proxy checkpoint system to allow resumption.

Usage:
    from feature_breakdown import break_down_features, suggest_parallelism

    tasks = [
        {"name": "auth", "deps": []},
        {"name": "profile", "deps": ["auth"]},
        {"name": "payments", "deps": ["auth"]},
        {"name": "notifications", "deps": []},
    ]

    features = break_down_features(tasks)
    parallel_groups = suggest_parallelism(features)

The module is deliberately lightweight – it only provides the data structures
and simple algorithms needed by the experiment runner.
\"\"\"

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Iterable
import json
import os

# ----------------------------------------------------------------------
# Core data structures
# ----------------------------------------------------------------------

@dataclass
class Feature:
    \"\"\"Represents a single feature/component to be planned and executed.\"\"\"
    name: str
    deps: Set[str] = field(default_factory=set)   # other feature names this one depends on

    def is_independent(self) -> bool:
        \"\"\"Return True if the feature has no dependencies.\"\"\"
        return not self.deps


@dataclass
class FeaturePlanner:
    \"\"\"Placeholder for a planner that would receive a Feature and schedule work.\"\"\"
    feature: Feature

    def plan(self) -> Dict:
        \"\"\"Return a simple plan dict – in a real system this would be richer.\"\"\"
        return {
            "feature": self.feature.name,
            "dependencies": list(self.feature.deps),
            "status": "planned"
        }


# ----------------------------------------------------------------------
# Checkpoint integration (User Proxy)
# ----------------------------------------------------------------------


_CHECKPOINT_FILE = os.getenv("USER_PROXY_CHECKPOINT", "user_proxy_checkpoint.json")


def _load_checkpoint() -> Dict[str, Dict]:
    \"\"\"Load the checkpoint file if it exists, otherwise return an empty dict.\"\"\"
    if os.path.isfile(_CHECKPOINT_FILE):
        try:
            with open(_CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            # Corrupt checkpoint – start fresh
            return {}
    return {}


def _save_checkpoint(state: Dict[str, Dict]) -> None:
    \"\"\"Persist the current planning state to the checkpoint file.\"\"\"
    with open(_CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def integrate_checkpoint(planners: List[FeaturePlanner]) -> List[FeaturePlanner]:
    \"\"\"Update planners with any previously saved state.

    Features that were already planned will keep their existing plan;
    new features are added fresh.
    \"\"\"
    checkpoint = _load_checkpoint()
    updated: List[FeaturePlanner] = []

    for planner in planners:
        name = planner.feature.name
        if name in checkpoint:
            # Restore previous plan (could be extended to more fields)
            planner_state = checkpoint[name]
            # For now we only keep the status; real logic could merge more.
            planner.plan()["status"] = planner_state.get("status", "planned")
        else:
            # New entry – add to checkpoint
            checkpoint[name] = planner.plan()
        updated.append(planner)

    _save_checkpoint(checkpoint)
    return updated


# ----------------------------------------------------------------------
# Feature breakdown & parallelism suggestion
# ----------------------------------------------------------------------


def break_down_features(task_definitions: Iterable[Dict]) -> List[Feature]:
    \"\"\"Convert raw task definitions into Feature objects.

    Each task definition must contain:
        - ``name``: unique identifier
        - ``deps``: list of names this task depends on (optional)

    Example input:
        [
            {"name": "auth", "deps": []},
            {"name": "profile", "deps": ["auth"]},
        ]
    \"\"\"
    features: List[Feature] = []
    for task in task_definitions:
        name = task["name"]
        deps = set(task.get("deps", []))
        features.append(Feature(name=name, deps=deps))
    return features


def _topological_sort(features: List[Feature]) -> List[Feature]:
    \"\"\"Return features in a topologically sorted order.

    Raises ValueError if a circular dependency is detected.
    \"\"\"
    name_to_feature = {f.name: f for f in features}
    visited: Set[str] = set()
    temp_mark: Set[str] = set()
    result: List[Feature] = []

    def visit(node_name: str) -> None:
        if node_name in visited:
            return
        if node_name in temp_mark:
            raise ValueError(f"Circular dependency detected at {node_name}")
        temp_mark.add(node_name)
        for dep in name_to_feature[node_name].deps:
            if dep not in name_to_feature:
                raise ValueError(f"Missing dependency {dep} for feature {node_name}")
            visit(dep)
        temp_mark.remove(node_name)
        visited.add(node_name)
        result.append(name_to_feature[node_name])

    for feature in features:
        visit(feature.name)

    return result


def suggest_parallelism(features: List[Feature]) -> List[Set[str]]:
    \"\"\"Group features that can be executed in parallel.

    The algorithm walks the topologically sorted list and creates
    execution layers.  All features in the same layer have no mutual
    dependencies and therefore may run concurrently.

    Returns:
        A list where each element is a set of feature names that can run together.
    \"\"\"
    sorted_features = _topological_sort(features)
    layers: List[Set[str]] = []

    # Mapping from feature name to the layer index it was placed in
    placed_layer: Dict[str, int] = {}

    for feat in sorted_features:
        # Determine the highest layer index of its dependencies
        max_dep_layer = -1
        for dep in feat.deps:
            max_dep_layer = max(max_dep_layer, placed_layer[dep])
        # This feature can be placed in the next layer after its deepest dependency
        target_layer = max_dep_layer + 1
        if target_layer >= len(layers):
            layers.append(set())
        layers[target_layer].add(feat.name)
        placed_layer[feat.name] = target_layer

    return layers


def prepare_planners(features: List[Feature]) -> List[FeaturePlanner]:
    \"\"\"Create a FeaturePlanner for each feature and integrate checkpoint state.\"\"\"
    planners = [FeaturePlanner(feature=f) for f in features]
    return integrate_checkpoint(planners)


# ----------------------------------------------------------------------
# Example entry point (not executed on import)
# ----------------------------------------------------------------------


def _example_usage() -> None:
    example_tasks = [
        {"name": "auth", "deps": []},
        {"name": "profile", "deps": ["auth"]},
        {"name": "payments", "deps": ["auth"]},
        {"name": "notifications", "deps": []},
        {"name": "analytics", "deps": ["payments", "profile"]},
    ]

    feats = break_down_features(example_tasks)
    planners = prepare_planners(feats)
    parallel_groups = suggest_parallelism(feats)

    print("Parallel execution groups:")
    for i, group in enumerate(parallel_groups):
        print(f\"Layer {i}: {sorted(group)}\")

    # Show planner snapshots
    for p in planners:
        print(p.plan())


if __name__ == "__main__":
    # Running this module directly will demonstrate the breakdown logic.
    _example_usage()