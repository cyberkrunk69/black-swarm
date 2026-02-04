"""
feature_breakdown.py

Utility for breaking a project into independent features/components,
assigning each to a FeaturePlanner, and suggesting possible parallel execution
paths. Includes a simple UserProxy checkpoint integration.
"""

from __future__ import annotations
from typing import List, Dict, Set, Tuple
import itertools
import json
import logging

logger = logging.getLogger(__name__)


class UserProxy:
    """
    Simple placeholder for a user proxy checkpoint.
    In a real system this would verify user permissions, context, etc.
    """

    @staticmethod
    def checkpoint(user_id: str, action: str) -> bool:
        # Placeholder logic – always allow in this stub.
        # Replace with real authentication/authorization checks.
        logger.debug(f"UserProxy checkpoint: user_id={user_id}, action={action}")
        return True


class Feature:
    """
    Represents a single feature/component of a larger project.
    """

    def __init__(self, name: str, dependencies: List[str] = None):
        self.name = name
        self.dependencies = set(dependencies or [])
        self.planner: FeaturePlanner | None = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "dependencies": list(self.dependencies),
            "planner": self.planner.name if self.planner else None,
        }

    def __repr__(self):
        return f"<Feature {self.name} deps={self.dependencies}>"


class FeaturePlanner:
    """
    Holds planning details for a Feature.
    """

    def __init__(self, name: str, resources: Dict = None):
        self.name = name
        self.resources = resources or {}

    def plan(self, feature: Feature) -> None:
        """
        Attach this planner to a feature.
        """
        feature.planner = self

    def to_dict(self) -> Dict:
        return {"name": self.name, "resources": self.resources}


class FeatureBreakdown:
    """
    Core class that:
      * Accepts raw feature definitions.
      * Assigns each feature to a FeaturePlanner.
      * Computes which features can be executed in parallel.
      * Provides a checkpoint via UserProxy before exposing results.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.features: Dict[str, Feature] = {}
        self.planners: Dict[str, FeaturePlanner] = {}

    # --------------------------------------------------------------------- #
    # Feature registration
    # --------------------------------------------------------------------- #
    def add_feature(self, name: str, dependencies: List[str] = None) -> Feature:
        if name in self.features:
            raise ValueError(f"Feature '{name}' already exists.")
        feature = Feature(name, dependencies)
        self.features[name] = feature
        logger.debug(f"Added {feature}")
        return feature

    # --------------------------------------------------------------------- #
    # Planner registration and assignment
    # --------------------------------------------------------------------- #
    def add_planner(self, name: str, resources: Dict = None) -> FeaturePlanner:
        if name in self.planners:
            raise ValueError(f"Planner '{name}' already exists.")
        planner = FeaturePlanner(name, resources)
        self.planners[name] = planner
        logger.debug(f"Added planner {planner.name}")
        return planner

    def assign_planner(self, feature_name: str, planner_name: str) -> None:
        if feature_name not in self.features:
            raise KeyError(f"Feature '{feature_name}' not found.")
        if planner_name not in self.planners:
            raise KeyError(f"Planner '{planner_name}' not found.")
        planner = self.planners[planner_name]
        planner.plan(self.features[feature_name])
        logger.debug(f"Assigned planner '{planner_name}' to feature '{feature_name}'")

    # --------------------------------------------------------------------- #
    # Parallelism analysis
    # --------------------------------------------------------------------- #
    def _build_dependency_graph(self) -> Dict[str, Set[str]]:
        """
        Returns a dict mapping each feature to the set of features that must
        complete before it can start.
        """
        graph = {name: set(feat.dependencies) for name, feat in self.features.items()}
        logger.debug(f"Dependency graph: {graph}")
        return graph

    def suggest_parallel_groups(self) -> List[Set[str]]:
        """
        Returns a list of sets, each set containing feature names that can run
        concurrently. The algorithm performs a simple topological layering.
        """
        graph = self._build_dependency_graph()
        remaining = set(self.features.keys())
        layers: List[Set[str]] = []

        while remaining:
            # Find all nodes with no unmet dependencies
            ready = {name for name in remaining if not graph[name] & remaining}
            if not ready:
                raise RuntimeError("Cyclic dependency detected among remaining features: "
                                   f"{remaining}")
            layers.append(ready)
            logger.debug(f"Layer {len(layers)} ready: {ready}")
            remaining -= ready

        logger.info(f"Parallel groups (layers): {layers}")
        return layers

    # --------------------------------------------------------------------- #
    # Export / checkpoint
    # --------------------------------------------------------------------- #
    def export_plan(self) -> str:
        """
        Returns a JSON representation of the feature breakdown after performing
        a UserProxy checkpoint.
        """
        if not UserProxy.checkpoint(self.user_id, action="export_plan"):
            raise PermissionError("UserProxy checkpoint failed for export_plan.")

        data = {
            "features": {name: feat.to_dict() for name, feat in self.features.items()},
            "planners": {name: planner.to_dict() for name, planner in self.planners.items()},
            "parallel_groups": [
                list(group) for group in self.suggest_parallel_groups()
            ],
        }
        json_repr = json.dumps(data, indent=2)
        logger.debug(f"Exported plan JSON: {json_repr}")
        return json_repr


# ------------------------------------------------------------------------- #
# Example usage (would be removed or placed under a __main__ guard in prod)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    fb = FeatureBreakdown(user_id="example_user")

    # Define features
    fb.add_feature("auth")
    fb.add_feature("profile", dependencies=["auth"])
    fb.add_feature("dashboard", dependencies=["auth"])
    fb.add_feature("notifications", dependencies=["profile", "dashboard"])
    fb.add_feature("settings", dependencies=["profile"])

    # Define planners
    fb.add_planner("backend")
    fb.add_planner("frontend")

    # Assign planners
    fb.assign_planner("auth", "backend")
    fb.assign_planner("profile", "backend")
    fb.assign_planner("dashboard", "frontend")
    fb.assign_planner("notifications", "frontend")
    fb.assign_planner("settings", "backend")

    # Output plan
    print(fb.export_plan())