"""
IIT‑inspired Self‑Model Metrics

This module provides a lightweight implementation of Integrated Information Theory (IIT)
inspired metrics for evaluating a self‑model. The primary goal is to compute a scalar
value (phi) that quantifies the degree of integration within the self‑model and to
store the result in the agent's ``self.experience`` dictionary under the key
``'self_model_phi'``.

The implementation is deliberately simple and does not aim to be a full IIT
calculation (which would require exhaustive partitioning of the system's state
space). Instead, it uses a proxy based on mutual information between the
self‑model's internal representation and its predictions of future observations.
This proxy captures the intuition that a highly integrated self‑model should
explain future observations better than a collection of independent parts.

Usage
-----

>>> from iit_self_model_metrics import SelfModelMetric
>>> metric = SelfModelMetric(agent)
>>> metric.update(observation, prediction)
>>> # After several updates
>>> metric.finalize()
>>> print(agent.experience['self_model_phi'])
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np


class SelfModelMetric:
    """
    Compute an IIT‑inspired integration metric (phi) for a self‑model.

    Parameters
    ----------
    agent : Any
        The agent object that holds a ``experience`` attribute (a mutable mapping).
        The computed phi will be stored as ``agent.experience['self_model_phi']``.
    """

    def __init__(self, agent: Any):
        if not hasattr(agent, "experience") or not isinstance(agent.experience, dict):
            raise AttributeError(
                "Agent must have an attribute 'experience' of type dict."
            )
        self.agent = agent
        # Store joint and marginal counts for a simple mutual information estimate
        self.joint_counts: Dict[Tuple[Any, Any], int] = defaultdict(int)
        self.obs_counts: Dict[Any, int] = defaultdict(int)
        self.pred_counts: Dict[Any, int] = defaultdict(int)
        self.total: int = 0

    def _hashable(self, value: Any) -> Any:
        """
        Convert a value into a hashable representation.
        Numpy arrays are converted to tuples; other types are returned unchanged.
        """
        if isinstance(value, np.ndarray):
            return tuple(value.tolist())
        if isinstance(value, (list, tuple)):
            return tuple(value)
        return value

    def update(self, observation: Any, prediction: Any) -> None:
        """
        Register a single observation/prediction pair.

        Parameters
        ----------
        observation : Any
            The actual observation received from the environment.
        prediction : Any
            The self‑model's prediction for the next observation.
        """
        o = self._hashable(observation)
        p = self._hashable(prediction)

        self.joint_counts[(o, p)] += 1
        self.obs_counts[o] += 1
        self.pred_counts[p] += 1
        self.total += 1

    def _mutual_information(self) -> float:
        """
        Compute the empirical mutual information I(O;P) based on the collected counts.
        I(O;P) = Σ_{o,p} P(o,p) * log( P(o,p) / (P(o)P(p)) )
        """
        if self.total == 0:
            return 0.0

        mi = 0.0
        for (o, p), joint in self.joint_counts.items():
            p_op = joint / self.total
            p_o = self.obs_counts[o] / self.total
            p_p = self.pred_counts[p] / self.total
            # Guard against zero probabilities (should not happen with counts)
            if p_op > 0 and p_o > 0 and p_p > 0:
                mi += p_op * math.log(p_op / (p_o * p_p), 2)  # bits
        return mi

    def finalize(self) -> None:
        """
        Compute the final phi metric and store it in ``self.agent.experience``.

        The metric used here is a simple normalized mutual information:

            phi = I(O;P) / H(O)

        where H(O) is the entropy of the observations. This yields a value in [0,1],
        with higher values indicating a more integrated self‑model.
        """
        if self.total == 0:
            phi = 0.0
        else:
            # Observation entropy H(O)
            h_obs = 0.0
            for count in self.obs_counts.values():
                p_o = count / self.total
                h_obs -= p_o * math.log(p_o, 2)

            mi = self._mutual_information()
            phi = mi / h_obs if h_obs > 0 else 0.0

        # Store the result
        self.agent.experience["self_model_phi"] = phi

        # Optional: keep raw statistics for debugging
        self.agent.experience.setdefault("self_model_stats", {})
        self.agent.experience["self_model_stats"].update(
            {
                "total_pairs": self.total,
                "mutual_information_bits": self._mutual_information(),
                "observation_entropy_bits": h_obs if self.total > 0 else 0.0,
            }
        )