"""
consensus_node.py

Implements the **ConsensusNode** – a simple multi‑model aggregator that can
produce a consensus output from a collection of model callables.

Supported consensus strategies:
* ``majority`` – categorical voting (most common label).
* ``average`` – numeric averaging (mean of floats or vectors).
* ``weighted`` – same as average but respects a per‑model weight list.

The node is deliberately lightweight, type‑annotated and fully unit‑tested.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass
from typing import Any, Callable, List, Sequence, Tuple, Union


ConsensusStrategy = Union["majority", "average", "weighted"]


@dataclass
class ModelSpec:
    """
    Immutable wrapper for a model callable.

    Attributes
    ----------
    name: str
        Human‑readable identifier.
    predict: Callable[..., Any]
        Callable that returns a prediction when invoked.
    weight: float, optional
        Used only for the ``weighted`` strategy.
    """
    name: str
    predict: Callable[..., Any]
    weight: float = 1.0


class ConsensusNode:
    """
    Aggregate predictions from multiple models according to a chosen strategy.
    """

    def __init__(
        self,
        models: Sequence[ModelSpec],
        strategy: ConsensusStrategy = "majority",
    ) -> None:
        if not models:
            raise ValueError("At least one model must be supplied")
        self.models = list(models)
        if strategy not in {"majority", "average", "weighted"}:
            raise ValueError(f"Unsupported strategy '{strategy}'")
        self.strategy = strategy

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def predict(self, *args: Any, **kwargs: Any) -> Any:
        """
        Run each model's ``predict`` method with the supplied arguments and
        return the consensus result.
        """
        predictions = [model.predict(*args, **kwargs) for model in self.models]

        if self.strategy == "majority":
            return self._majority_vote(predictions)
        if self.strategy == "average":
            return self._average(predictions)
        # weighted
        return self._weighted_average(predictions)

    # --------------------------------------------------------------------- #
    # Strategy implementations
    # --------------------------------------------------------------------- #
    @staticmethod
    def _majority_vote(predictions: List[Any]) -> Any:
        """
        Return the most common element. If a tie occurs, the first encountered
        element among the tied candidates is returned (deterministic).
        """
        counter = collections.Counter(predictions)
        most_common = counter.most_common()
        if not most_common:
            raise ValueError("No predictions to vote on")
        top_count = most_common[0][1]
        ties = [item for item, cnt in most_common if cnt == top_count]
        # Preserve original order for deterministic tie‑break
        for pred in predictions:
            if pred in ties:
                return pred
        return most_common[0][0]  # fallback (should never hit)

    @staticmethod
    def _average(predictions: List[Any]) -> Any:
        """
        Compute a simple arithmetic mean. Supports:
        * Scalars (int/float)
        * Sequences of numbers (list/tuple)
        """
        if not predictions:
            raise ValueError("No predictions to average")

        first = predictions[0]
        if isinstance(first, (int, float)):
            return sum(predictions) / len(predictions)  # type: ignore[return-value]

        # Assume iterable of numbers
        length = len(first)
        if any(len(p) != length for p in predictions):
            raise ValueError("All predictions must have the same length for averaging")

        summed = [0.0] * length
        for pred in predictions:
            for i, val in enumerate(pred):
                summed[i] += float(val)
        return [v / len(predictions) for v in summed]

    def _weighted_average(self, predictions: List[Any]) -> Any:
        """
        Weighted arithmetic mean using the ``weight`` attribute from each
        ``ModelSpec``. Weight list must sum to > 0.
        """
        if not predictions:
            raise ValueError("No predictions to average")

        weights = [model.weight for model in self.models]
        total_weight = sum(weights)
        if total_weight <= 0:
            raise ValueError("Sum of weights must be positive")

        first = predictions[0]
        if isinstance(first, (int, float)):
            weighted_sum = sum(p * w for p, w in zip(predictions, weights))
            return weighted_sum / total_weight

        # Iterable case
        length = len(first)
        if any(len(p) != length for p in predictions):
            raise ValueError("All predictions must have the same length for weighted averaging")

        weighted = [0.0] * length
        for pred, w in zip(predictions, weights):
            for i, val in enumerate(pred):
                weighted[i] += float(val) * w
        return [v / total_weight for v in weighted]