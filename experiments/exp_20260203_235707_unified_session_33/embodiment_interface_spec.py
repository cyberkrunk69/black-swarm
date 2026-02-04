"""
embodiment_interface_spec.py

Specification of the abstract Embodiment Interface used by the AGI core.
Only the interface (no concrete implementation) is defined here.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

# ----------------------------------------------------------------------
# Basic data structures
# ----------------------------------------------------------------------
@dataclass
class Observation:
    """
    Container for raw sensor data.
    Fields can be extended by concrete back‑ends.
    """
    rgb: Any = None          # e.g., np.ndarray (H, W, 3)
    depth: Any = None        # e.g., np.ndarray (H, W)
    joint_positions: List[float] | None = None
    joint_velocities: List[float] | None = None
    tactile: Any = None      # optional tactile sensor reading
    extra: Dict[str, Any] = None   # catch‑all for custom sensors


@dataclass
class State:
    """
    Normalized state representation consumed by the language model.
    """
    vector: List[float]      # flattened numeric representation
    metadata: Dict[str, Any] = None


@dataclass
class Action:
    """
    Primitive action definition.
    """
    name: str                           # e.g., "MOVE_JOINT", "GRIPPER_CLOSE"
    parameters: Dict[str, Any] = None   # joint indices, target pose, etc.


# ----------------------------------------------------------------------
# Abstract Interface
# ----------------------------------------------------------------------
class EmbodimentInterface(ABC):
    """
    Abstract base class defining the contract between the AGI core
    and any embodied backend (simulator or real robot).
    """

    @abstractmethod
    def reset(self) -> Observation:
        """
        Reset the environment / robot to a known initial state.
        Returns the first raw observation.
        """
        ...

    @abstractmethod
    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict]:
        """
        Apply a single primitive action.

        Returns:
            observation (Observation): new raw sensor data
            reward (float): scalar feedback for the step
            done (bool): whether the episode terminated
            info (dict): auxiliary debugging information
        """
        ...

    @abstractmethod
    def get_observation(self) -> Observation:
        """
        Query the current raw observation without advancing the simulation.
        """
        ...

    @abstractmethod
    def encode_state(self, obs: Observation) -> State:
        """
        Convert a raw Observation into the normalized State representation
        expected by the language model.
        """
        ...

    @abstractmethod
    def render(self, mode: str = "rgb_array") -> Any:
        """
        Optional visualisation for debugging.
        mode can be "rgb_array", "human", etc.
        """
        ...

    # ------------------------------------------------------------------
    # Optional helper methods (can be left as no‑ops in simple sims)
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Release any resources (simulation windows, ROS nodes, etc.)."""
        pass

    def seed(self, seed: int) -> None:
        """Set deterministic seed for the backend, if supported."""
        pass