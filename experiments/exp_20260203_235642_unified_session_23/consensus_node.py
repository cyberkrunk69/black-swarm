"""
ConsensusNode – Simple multi‑model agreement engine.

The component aggregates predictions from a collection of model callables.
Two consensus strategies are provided:

* ``majority`` – for categorical outputs (string/int). Returns the most
  common prediction; ties are broken by deterministic sorting.
* ``average`` – for numeric outputs (float/int). Returns the arithmetic mean.

The implementation is deliberately lightweight and depends only on the
standard library.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Dict, List, Union


class ConsensusNode:
    """
    Holds a registry of model callables and produces a consensus output for a
    given input.
    """

    def __init__(self, strategy: str = "majority"):
        if strategy not in {"majority", "average"}:
            raise ValueError("strategy must be 'majority' or 'average'")
        self.strategy = strategy
        self._models: Dict[str, Callable[[Any], Any]] = {}

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def register_model(self, name: str, fn: Callable[[Any], Any]) -> None:
        """
        Register a model callable.

        Parameters
        ----------
        name: str
            Identifier for the model.
        fn: Callable[[Any], Any]
            Function that accepts an input and returns a prediction.
        """
        if name in self._models:
            raise ValueError(f"Model '{name}' already registered.")
        self._models[name] = fn

    def consensus(self, input_data: Any) -> Any:
        """
        Run all registered models on *input_data* and return a consensus value.

        Returns
        -------
        Any
            Consensus prediction according to the selected strategy.
        """
        if not self._models:
            raise RuntimeError("No models registered.")

        predictions = [fn(input_data) for fn in self._models.values()]

        if self.strategy == "majority":
            return self._majority_vote(predictions)
        else:  # average
            return self._average(predictions)

    # --------------------------------------------------------------------- #
    # Private helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _majority_vote(values: List[Any]) -> Any:
        counter = Counter(values)
        most_common = counter.most_common()
        max_count = most_common[0][1]
        # Gather all items with the same max count (possible tie)
        tied = [val for val, cnt in most_common if cnt == max_count]
        # Deterministic tie‑breaker: sorted order
        return sorted(tied)[0]

    @staticmethod
    def _average(values: List[Union[int, float]]) -> float:
        numeric = [float(v) for v in values]
        return sum(numeric) / len(numeric)