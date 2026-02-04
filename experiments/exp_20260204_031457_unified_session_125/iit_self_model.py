"""
iit_self_model.py

Implementation of a lightweight Integrated Information Theory (IIT) inspired
self‑model metric suite. The metrics are deliberately simplified for
demonstration purposes while preserving the core idea of measuring
intrinsic causal power (Φ) of a system’s internal states.

Results are stored in the global ``self.experience`` dictionary under the
key ``"iit_metrics"`` so that downstream components can retrieve them.

Usage
-----
>>> from iit_self_model import run_iit_metrics
>>> state = [0, 1, 1, 0]
>>> connectivity = [
...     [0, 1, 0, 0],
...     [1, 0, 1, 0],
...     [0, 1, 0, 1],
...     [0, 0, 1, 0],
... ]
>>> run_iit_metrics(state, connectivity)
"""

from __future__ import annotations
import itertools
import math
from typing import List, Tuple, Dict, Any

# The global ``self`` object is provided by the framework.
# It is expected to expose an ``experience`` attribute that behaves like a dict.
try:
    # The actual import path may vary depending on the host environment.
    from self_module import self as global_self  # type: ignore
except Exception as e:
    raise ImportError(
        "Unable to import the global 'self' object. Ensure that a module named "
        "'self_module' exposing a 'self' instance with an 'experience' dict is "
        "available in the runtime environment."
    ) from e


def _entropy(probabilities: List[float]) -> float:
    """Shannon entropy for a probability distribution."""
    return -sum(p * math.log2(p) for p in probabilities if p > 0)


def _binary_entropy(p: float) -> float:
    """Entropy of a binary variable with probability p of being 1."""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def _state_probability(state: Tuple[int, ...]) -> float:
    """
    For demonstration we treat each binary state as equally likely.
    In a real implementation this would be derived from dynamics or empirical data.
    """
    return 1.0 / (2 ** len(state))


def _partition_subsets(n: int) -> List[Tuple[Tuple[int, ...], Tuple[int, ...]]]:
    """
    Generate all bipartitions of a set of ``n`` elements, excluding the trivial
    partitions (empty set or full set). Returns a list of index tuples.
    """
    indices = tuple(range(n))
    partitions = []
    # Enumerate subsets of size 1 .. n-1 and pair with its complement.
    for r in range(1, n // 2 + 1):
        for subset in itertools.combinations(indices, r):
            complement = tuple(i for i in indices if i not in subset)
            partitions.append((subset, complement))
    return partitions


def _effective_information(
    partition: Tuple[Tuple[int, ...], Tuple[int, ...]],
    state: Tuple[int, ...],
    connectivity: List[List[int]],
) -> float:
    """
    Compute a very simplified version of Effective Information (EI) for a
    bipartition of the system. EI approximates the causal power that the
    parts have over each other.

    The calculation follows:
        EI = H(part_A) + H(part_B) - H(part_A, part_B | partition)

    For this toy implementation we approximate conditional entropy by assuming
    independence across the cut, which yields a lower bound on EI.
    """
    part_a, part_b = partition
    # Marginal probabilities (binary, uniform)
    ha = sum(_binary_entropy(0.5) for _ in part_a)  # each element is binary
    hb = sum(_binary_entropy(0.5) for _ in part_b)

    # Joint entropy assuming independence across the cut
    # (i.e., the cut destroys any cross‑part correlations)
    h_joint = ha + hb

    # Effective information is the reduction in uncertainty due to the cut:
    ei = (ha + hb) - h_joint
    return ei  # This will be zero with the naive independence assumption,
                # but the function is kept for structural completeness.


def _phi(state: Tuple[int, ...], connectivity: List[List[int]]) -> float:
    """
    Compute a highly simplified Φ (phi) value for the whole system.
    The algorithm enumerates all bipartitions, computes the effective
    information for each, and returns the minimum EI (the “information
    bottleneck”) as a proxy for Φ.
    """
    n = len(state)
    if n == 0:
        return 0.0

    partitions = _partition_subsets(n)
    if not partitions:
        return 0.0

    ei_values = [
        _effective_information(partition, state, connectivity) for partition in partitions
    ]
    # In a proper IIT calculation Φ is the *minimum* EI across all cuts.
    phi_value = min(ei_values)
    return phi_value


def compute_iit_metrics(
    state: List[int],
    connectivity: List[List[int]],
) -> Dict[str, Any]:
    """
    Public API to compute a set of IIT‑inspired metrics.

    Parameters
    ----------
    state : List[int]
        Binary state vector of the system (e.g., [0,1,1,0]).
    connectivity : List[List[int]]
        Adjacency matrix (0/1) describing directed connections between
        elements. ``connectivity[i][j] == 1`` means element *i* influences *j*.

    Returns
    -------
    dict
        Dictionary containing:
        - ``phi``: Simplified integrated information.
        - ``entropy``: Shannon entropy of the full state (assuming uniform
          distribution over all possible states of the same size).
        - ``effective_information``: List of EI values for each bipartition.
    """
    if not all(bit in (0, 1) for bit in state):
        raise ValueError("State vector must be binary (0 or 1).")
    if len(state) != len(connectivity):
        raise ValueError("State length must match connectivity matrix dimensions.")

    # Convert to immutable tuple for hashing / internal use
    state_tuple = tuple(state)

    # Compute full‑system entropy (uniform distribution assumption)
    prob = _state_probability(state_tuple)
    entropy = _entropy([prob, 1 - prob]) if prob not in (0, 1) else 0.0

    # Compute Φ (phi) using the simplified routine
    phi_val = _phi(state_tuple, connectivity)

    # Compute EI for each bipartition (use same helper)
    partitions = _partition_subsets(len(state))
    ei_list = [
        _effective_information(partition, state_tuple, connectivity) for partition in partitions
    ]

    return {
        "phi": phi_val,
        "entropy": entropy,
        "effective_information": ei_list,
    }


def _store_in_experience(metrics: Dict[str, Any]) -> None:
    """
    Store the computed metrics in the global ``self.experience`` dictionary
    under the ``"iit_metrics"`` key. If the key already exists, the new
    metrics are merged (new values overwrite old ones with the same sub‑key).
    """
    if not hasattr(global_self, "experience"):
        raise AttributeError("Global 'self' object does not have an 'experience' attribute.")

    # Ensure the experience dict exists
    if not isinstance(global_self.experience, dict):
        raise TypeError("'self.experience' must be a dictionary.")

    existing = global_self.experience.get("iit_metrics", {})
    if not isinstance(existing, dict):
        existing = {}

    # Merge dictionaries (shallow merge is sufficient for this simple case)
    merged = {**existing, **metrics}
    global_self.experience["iit_metrics"] = merged


def run_iit_metrics(state: List[int], connectivity: List[List[int]]) -> Dict[str, Any]:
    """
    Convenience wrapper that computes the IIT metrics and automatically
    stores them in ``self.experience``.

    Returns the metric dictionary for immediate inspection.
    """
    metrics = compute_iit_metrics(state, connectivity)
    _store_in_experience(metrics)
    return metrics


# If the module is executed directly, run a quick demo.
if __name__ == "__main__":
    demo_state = [0, 1, 1, 0]
    demo_connectivity = [
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [0, 0, 1, 0],
    ]
    result = run_iit_metrics(demo_state, demo_connectivity)
    print("IIT metrics computed and stored in self.experience:")
    print(result)