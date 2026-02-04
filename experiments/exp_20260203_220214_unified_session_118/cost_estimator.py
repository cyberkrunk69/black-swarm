"""
Cost Estimator Module

Provides utilities to predict the computational cost of tasks based on
task length, complexity score, and historical data. It also offers simple
budget checks and warnings.

Usage:
    from cost_estimator import CostEstimator

    estimator = CostEstimator(budget=1000)  # total budget units
    predicted = estimator.predict(task_length=120, complexity=3.5, similar_tasks=[...])
    if estimator.can_execute(predicted):
        # run the task
        pass
    else:
        # skip or defer the task
        pass
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class HistoricalTask:
    """Record of a previously executed task."""
    length: int          # e.g., number of lines or seconds
    complexity: float    # arbitrary complexity score
    cost: float          # actual cost incurred


@dataclass
class CostEstimator:
    """Predicts task cost and enforces a simple budget."""
    budget: float                                 # total budget available
    spent: float = 0.0                            # cost already used
    history: List[HistoricalTask] = field(default_factory=list)

    # Tunable coefficients (could be calibrated with real data)
    _base_rate: float = 0.1       # cost per unit length
    _complexity_factor: float = 2.0  # multiplier per complexity point

    def _similarity(self, length: int, complexity: float, hist: HistoricalTask) -> float:
        """Simple similarity metric between a new task and a historical one."""
        length_diff = abs(length - hist.length) / max(1, hist.length)
        comp_diff = abs(complexity - hist.complexity) / max(1e-6, hist.complexity)
        # Inverse of distance, capped at 1.0
        similarity = 1.0 / (1.0 + length_diff + comp_diff)
        return similarity

    def _aggregate_historical_cost(self, length: int, complexity: float) -> Optional[float]:
        """Estimate cost from historical tasks using weighted average."""
        if not self.history:
            return None

        weighted_sum = 0.0
        weight_total = 0.0
        for hist in self.history:
            sim = self._similarity(length, complexity, hist)
            weighted_sum += sim * hist.cost
            weight_total += sim

        if weight_total == 0:
            return None
        return weighted_sum / weight_total

    def predict(self,
                task_length: int,
                complexity: float,
                similar_tasks: Optional[List[HistoricalTask]] = None) -> float:
        """
        Predict the cost of a task.

        Parameters
        ----------
        task_length : int
            Measure of task size (e.g., number of lines, seconds, tokens).
        complexity : float
            Arbitrary score representing algorithmic or logical complexity.
        similar_tasks : Optional[List[HistoricalTask]]
            Additional historical tasks to consider for this prediction.
            If provided, they are temporarily added to the history for weighting.

        Returns
        -------
        float
            Predicted cost units.
        """
        # Base linear model
        base_estimate = self._base_rate * task_length + self._complexity_factor * complexity

        # Incorporate historical data if available
        if similar_tasks:
            original_history = self.history.copy()
            self.history.extend(similar_tasks)
            hist_estimate = self._aggregate_historical_cost(task_length, complexity)
            self.history = original_history  # restore
        else:
            hist_estimate = self._aggregate_historical_cost(task_length, complexity)

        if hist_estimate is not None:
            # Blend model and history (50/50 weighting)
            predicted = (base_estimate + hist_estimate) / 2.0
        else:
            predicted = base_estimate

        logger.debug(
            "Cost prediction: length=%s, complexity=%s, base=%s, hist=%s => predicted=%s",
            task_length, complexity, base_estimate, hist_estimate, predicted
        )
        return predicted

    def can_execute(self, predicted_cost: float, warn_threshold: float = 0.9) -> bool:
        """
        Determine if a task can be executed under the remaining budget.

        Parameters
        ----------
        predicted_cost : float
            Cost predicted by `predict`.
        warn_threshold : float
            Fraction of remaining budget at which a warning is issued.

        Returns
        -------
        bool
            True if the task can be executed; False if it should be skipped.
        """
        remaining = self.budget - self.spent
        if predicted_cost > remaining:
            logger.warning(
                "Predicted cost %.2f exceeds remaining budget %.2f. Skipping task.",
                predicted_cost, remaining
            )
            return False

        if predicted_cost > warn_threshold * remaining:
            logger.info(
                "Predicted cost %.2f is approaching remaining budget %.2f.",
                predicted_cost, remaining
            )
        return True

    def record_execution(self, task_length: int, complexity: float, actual_cost: float) -> None:
        """
        Record the actual cost of a completed task for future predictions.

        Parameters
        ----------
        task_length : int
            Length of the executed task.
        complexity : float
            Complexity score used during execution.
        actual_cost : float
            Real cost incurred.
        """
        self.spent += actual_cost
        self.history.append(HistoricalTask(task_length, complexity, actual_cost))
        logger.info(
            "Recorded execution: length=%s, complexity=%s, cost=%s. Total spent: %s",
            task_length, complexity, actual_cost, self.spent
        )

    def reset(self) -> None:
        """Reset spent budget and historical data."""
        self.spent = 0.0
        self.history.clear()
        logger.info("CostEstimator reset.")