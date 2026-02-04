\"\"\"feature_breakdown.py
Utility to split a project into independent features/components, assign each to a
FeaturePlanner, suggest parallel execution groups, and integrate a User Proxy
checkpoint for state persistence.

The module is deliberately lightweight – it provides data structures and a
few helper functions that can be imported by higher‑level orchestration code.
\"\"\"

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Iterable, Tuple
import json
import pathlib


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

@dataclass
class Feature:
    \"\"\"A discrete unit of work.

    Attributes
    ----------
    name: str
        Human‑readable identifier.
    dependencies: Set[str]
        Names of other features that must complete before this one can start.
    metadata: Dict[str, str]
        Arbitrary key‑value pairs that can be used by planners or UI.
    \"\"\"
    name: str
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, str] = field(default_factory=dict)

    def is_ready(self, completed: Set[str]) -> bool:
        \"\"\"Return ``True`` if all dependencies are satisfied.\"
        return self.dependencies.issubset(completed)


@dataclass
class FeaturePlanner:
    \"\"\"Placeholder for a concrete planner implementation.

    In a real system this would encapsulate the logic for planning,
    scheduling, and executing a feature. Here we only store the feature
    and expose a ``plan`` stub.
    \"\"\"
    feature: Feature

    def plan(self) -> str:
        \"\"\"Return a textual representation of the plan.

        This stub can be replaced with richer behaviour (e.g. generating
        CI jobs, Dockerfiles, etc.).
        \"\"\"
        return f\"Plan for feature '{self.feature.name}' with deps {sorted(self.feature.dependencies)}\"


# ---------------------------------------------------------------------------
# Parallelism suggestion algorithm
# ---------------------------------------------------------------------------

def suggest_parallel_groups(features: Iterable[Feature]) -> List[Set[str]]:
    \"\"\"Group feature names into sets that can run in parallel.

    The algorithm is a simple topological‑layer walk:
    1. Find all features with no unsatisfied dependencies → first group.
    2. Remove those from the graph and repeat.

    Parameters
    ----------
    features: iterable of Feature
        The complete feature list.

    Returns
    -------
    List[Set[str]]
        Ordered list where each set may be executed concurrently.
    \"\"\"
    # Build lookup tables
    name_to_feature: Dict[str, Feature] = {f.name: f for f in features}
    remaining: Set[str] = set(name_to_feature)
    completed: Set[str] = set()
    groups: List[Set[str]] = []

    while remaining:
        # Features whose deps are all in completed
        ready = {name for name in remaining if name_to_feature[name].is_ready(completed)}
        if not ready:
            # Circular dependency – raise a clear error
            cycle = remaining
            raise RuntimeError(f\"Circular dependency detected among: {', '.join(cycle)}\")

        groups.append(ready)
        completed.update(ready)
        remaining.difference_update(ready)

    return groups


# ---------------------------------------------------------------------------
# User Proxy checkpoint integration
# ---------------------------------------------------------------------------

_CHECKPOINT_FILE = pathlib.Path(__file__).with_name("feature_breakdown_checkpoint.json")


def save_checkpoint(planners: List[FeaturePlanner]) -> None:
    \"\"\"Persist the current planning state to a JSON file.

    The checkpoint contains a list of feature names that have been planned.
    \"\"\"
    data = {
        "planned_features": [planner.feature.name for planner in planners]
    }
    _CHECKPOINT_FILE.write_text(json.dumps(data, indent=2))


def load_checkpoint() -> Set[str]:
    \"\"\"Load the checkpoint and return the set of already planned feature names.

    If the checkpoint file does not exist, an empty set is returned.
    \"\"\"
    if not _CHECKPOINT_FILE.is_file():
        return set()
    try:
        data = json.loads(_CHECKPOINT_FILE.read_text())
        return set(data.get("planned_features", []))
    except Exception:
        # Corrupt file – treat as no checkpoint
        return set()


# ---------------------------------------------------------------------------
# High‑level helper
# ---------------------------------------------------------------------------

def build_planners(features: Iterable[Feature]) -> List[FeaturePlanner]:
    \"\"\"Create a ``FeaturePlanner`` for each feature, respecting the checkpoint.\n\n    Features that appear in the checkpoint are considered already planned and
    are skipped.\n    \"\"\"
    planned = load_checkpoint()
    planners: List[FeaturePlanner] = []
    for f in features:
        if f.name in planned:
            continue
        planners.append(FeaturePlanner(feature=f))
    return planners


# ---------------------------------------------------------------------------
# Example usage (can be removed or guarded by __name__ check)
# ---------------------------------------------------------------------------

if __name__ == \"__main__\":  # pragma: no cover
    # Sample feature set
    sample_features = [
        Feature(name=\"auth\", dependencies=set()),
        Feature(name=\"api\", dependencies={\"auth\"}),
        Feature(name=\"frontend\", dependencies={\"api\"}),
        Feature(name=\"notifications\", dependencies={\"auth\"}),
        Feature(name=\"billing\", dependencies={\"api\", \"notifications\"}),
    ]

    # Determine parallel groups
    groups = suggest_parallel_groups(sample_features)
    print(\"Parallel execution groups (order matters):\")
    for idx, grp in enumerate(groups, 1):
        print(f\"  Group {idx}: {', '.join(sorted(grp))}\")

    # Build planners respecting any prior checkpoint
    planners = build_planners(sample_features)
    for planner in planners:
        print(planner.plan())

    # Persist state (example)
    save_checkpoint(planners)