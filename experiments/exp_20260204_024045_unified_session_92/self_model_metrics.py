"""
self_model_metrics.py

Implementation of a lightweight, IIT‑inspired self‑model metric suite.
The results are stored in the ``self.experience`` dictionary, which
acts as a persistent experience log for the agent.

The module provides:
* ``integrated_information`` – a simple proxy for Tononi's Φ.
* ``causal_complexity`` – an entropy‑based measure of the system's
  causal richness.
* ``log_self_experience`` – helper to push computed metrics into
  ``self.experience``.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np


def _validate_square_matrix(matrix: np.ndarray) -> None:
    """Ensure ``matrix`` is a 2‑D square ``np.ndarray``."""
    if not isinstance(matrix, np.ndarray):
        raise TypeError("Matrix must be a NumPy ndarray.")
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square (NxN).")


def integrated_information(connectivity: np.ndarray) -> float:
    """
    Compute a fast, approximate Integrated Information (Φ) for a
    connectivity matrix.

    The implementation follows a very coarse approximation that
    captures the spirit of IIT:
    * Off‑diagonal absolute weights represent causal influence between
      subsystems.
    * Φ is taken as the sum of those influences after normalising by the
      number of possible connections.

    Parameters
    ----------
    connectivity : np.ndarray
        Square matrix (N×N) of causal weights (e.g., synaptic strengths,
        transition probabilities, etc.). Diagonal entries are ignored.

    Returns
    -------
    float
        Approximate Φ value in the range ``[0, 1]``.
    """
    _validate_square_matrix(connectivity)

    n = connectivity.shape[0]
    # Remove self‑connections
    off_diag = connectivity.copy()
    np.fill_diagonal(off_diag, 0.0)

    total_influence = np.abs(off_diag).sum()
    max_possible = n * (n - 1)  # number of off‑diagonal entries

    phi = total_influence / max_possible if max_possible else 0.0
    # Clamp to [0, 1] for safety
    return max(0.0, min(1.0, phi))


def causal_complexity(states: Sequence[Sequence[float]]) -> float:
    """
    Estimate the causal complexity of a system from a series of state
    vectors using Shannon entropy.

    The idea mirrors IIT's notion that a system with many equally likely
    macro‑states possesses high causal richness.

    Parameters
    ----------
    states : Sequence[Sequence[float]]
        Iterable of state vectors (e.g., neural activations over time).

    Returns
    -------
    float
        Normalised entropy in the range ``[0, 1]``.
    """
    if not states:
        return 0.0

    # Flatten to a 2‑D array (time × features)
    arr = np.asarray(states, dtype=float)
    if arr.ndim != 2:
        raise ValueError("States must be a 2‑D sequence (time × features).")

    # Discretise each feature into bins using a simple histogram approach.
    # For speed we use 10 bins per dimension.
    bins = 10
    hist, _ = np.histogramdd(arr, bins=bins)

    # Convert histogram to probability distribution
    prob = hist / prob.sum() if (prob := hist).sum() != 0 else np.zeros_like(hist)

    # Shannon entropy
    eps = np.finfo(float).eps
    entropy = -np.sum(prob * np.log2(prob + eps))

    # Normalise by the maximum possible entropy (log2 of number of bins)
    max_entropy = np.log2(bins ** arr.shape[1])
    return entropy / max_entropy if max_entropy else 0.0


def log_self_experience(self_obj: Any, metrics: Dict[str, float]) -> None:
    """
    Record metric values into ``self_obj.experience``.  If the attribute
    does not exist, it is created as an empty dictionary.

    Parameters
    ----------
    self_obj : Any
        The agent / self‑model instance whose experience log is to be
        updated.
    metrics : dict
        Mapping of metric names to their computed float values.
    """
    if not hasattr(self_obj, "experience") or not isinstance(self_obj.experience, dict):
        setattr(self_obj, "experience", {})

    # Merge new metrics, preserving existing entries
    self_obj.experience.update(metrics)


# --------------------------------------------------------------------------- #
# Convenience wrapper – can be called from the agent loop
# --------------------------------------------------------------------------- #
def update_self_model_metrics(self_obj: Any,
                              connectivity: np.ndarray,
                              recent_states: Sequence[Sequence[float]]) -> None:
    """
    Compute IIT‑inspired metrics and store them in ``self_obj.experience``.

    This function is intended to be invoked periodically (e.g., each
    reasoning tick) to keep the self‑model's experience up‑to‑date.

    Parameters
    ----------
    self_obj : Any
        The agent instance containing (or to receive) the ``experience``
        attribute.
    connectivity : np.ndarray
        Square causal connectivity matrix for the agent's internal model.
    recent_states : Sequence[Sequence[float]]
        Recent internal state snapshots (time‑ordered).
    """
    phi = integrated_information(connectivity)
    complexity = causal_complexity(recent_states)

    log_self_experience(self_obj, {
        "integrated_information_phi": phi,
        "causal_complexity": complexity,
        "timestamp": getattr(self_obj, "current_time", None)  # optional
    })