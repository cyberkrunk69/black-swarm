"""
iit_self_model.py

Implementation of a lightweight, IIT‑inspired self‑model metric suite.
The primary goal is to compute an integrated information (Φ) estimate for a
given system state and store the result in the object's ``experience`` store.

The implementation is deliberately simple and avoids heavy external
dependencies – it uses NumPy for matrix operations and provides a clear
extension point for more sophisticated Φ calculations.
"""

from __future__ import annotations
from typing import Any, Dict, Tuple, List
import numpy as np
import itertools
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _mutual_information(x: np.ndarray, y: np.ndarray) -> float:
    """
    Compute the (empirical) mutual information between two binary vectors.

    Parameters
    ----------
    x, y : np.ndarray
        1‑D binary arrays of equal length.

    Returns
    -------
    float
        Mutual information in bits.
    """
    if x.shape != y.shape:
        raise ValueError("Input vectors must have the same shape")

    joint = np.histogram2d(x, y, bins=2)[0] / x.size
    px = joint.sum(axis=1)
    py = joint.sum(axis=0)

    # Avoid log(0) by masking zero entries
    nz = joint > 0
    mi = np.sum(joint[nz] * np.log2(joint[nz] / (px[:, None][nz] * py[None, :][nz])))
    return float(mi)


def integrated_information(state_matrix: np.ndarray) -> float:
    """
    Very coarse approximation of integrated information (Φ).

    The function evaluates all bipartitions of the system's units,
    computes the mutual information between the two halves, and returns
    the minimum information loss across partitions – a common proxy for Φ.

    Parameters
    ----------
    state_matrix : np.ndarray
        2‑D binary array with shape (time_steps, num_units). Each column
        represents the activity of a unit over time.

    Returns
    -------
    float
        Approximate Φ value (bits). Higher values indicate more integrated
        dynamics.
    """
    if state_matrix.ndim != 2:
        raise ValueError("state_matrix must be a 2‑D array (time_steps, num_units)")

    num_units = state_matrix.shape[1]
    if num_units < 2:
        logger.warning("Φ is undefined for a single‑unit system; returning 0.0")
        return 0.0

    # Pre‑compute marginal entropies for speed
    entropies = []
    for i in range(num_units):
        p = np.mean(state_matrix[:, i])
        if p in (0.0, 1.0):
            ent = 0.0
        else:
            ent = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
        entropies.append(ent)

    # Evaluate all non‑trivial bipartitions
    min_information_loss = np.inf
    units = list(range(num_units))
    # Only need to iterate over half the partitions (avoid complements)
    for r in range(1, num_units // 2 + 1):
        for left in itertools.combinations(units, r):
            right = tuple(u for u in units if u not in left)
            left_data = state_matrix[:, left]
            right_data = state_matrix[:, right]

            # Collapse each side to a single binary variable by majority vote
            left_majority = (np.mean(left_data, axis=1) >= 0.5).astype(int)
            right_majority = (np.mean(right_data, axis=1) >= 0.5).astype(int)

            mi = _mutual_information(left_majority, right_majority)
            # Information loss = sum of entropies - mutual information
            loss = sum(entropies[i] for i in left) + sum(entropies[i] for i in right) - mi
            if loss < min_information_loss:
                min_information_loss = loss

    # Guard against pathological cases
    phi = max(0.0, min_information_loss)
    logger.info(f"Computed approximate Φ = {phi:.4f} bits")
    return phi


class SelfModel:
    """
    Minimal self‑model container that records experiential metrics.

    The ``experience`` dictionary can be inspected by downstream components
    (e.g., logging, reinforcement loops) to retrieve the latest Φ estimate.
    """

    def __init__(self) -> None:
        self.experience: Dict[str, Any] = {}

    def evaluate(self, state_matrix: np.ndarray) -> float:
        """
        Compute Φ for the provided state matrix and store it in ``experience``.

        Parameters
        ----------
        state_matrix : np.ndarray
            Binary activity matrix with shape (time_steps, num_units).

        Returns
        -------
        float
            The computed Φ value.
        """
        phi = integrated_information(state_matrix)
        self.experience["phi"] = phi
        logger.debug(f"SelfModel experience updated: {self.experience}")
        return phi

    def get_experience(self) -> Dict[str, Any]:
        """
        Return a copy of the stored experience metrics.

        Returns
        -------
        dict
            Current experiential data.
        """
        return dict(self.experience)


# Example usage (can be removed or guarded by __name__ check in production)
if __name__ == "__main__":
    # Simulate a simple 8‑unit system over 100 time steps
    np.random.seed(42)
    simulated_states = np.random.randint(0, 2, size=(100, 8))
    model = SelfModel()
    phi_val = model.evaluate(simulated_states)
    print(f"Integrated information (Φ) ≈ {phi_val:.4f} bits")
    print("Experience store:", model.get_experience())