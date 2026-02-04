"""
Cost Estimator Module

Provides utilities to predict the computational cost of a task based on:
- task length (e.g., number of tokens or steps)
- complexity score (user‑defined metric)
- historical data from similar tasks

The estimator also checks against a remaining budget and can raise warnings
or skip execution when the predicted cost exceeds the budget.

Typical usage:

    from cost_estimator import predict_cost, check_budget

    predicted = predict_cost(task_length=1500, complexity=3.2, similar_tasks=[...])
    check_budget(predicted, remaining_budget=5000)

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import warnings
import logging

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

@dataclass
class HistoricalTask:
    """Record of a previously executed task."""
    length: int               # e.g., token count, steps, etc.
    complexity: float         # numeric complexity rating
    cost: float               # actual cost incurred (e.g., CPU seconds, monetary units)


# --------------------------------------------------------------------------- #
# Core estimation logic
# --------------------------------------------------------------------------- #

def _average_cost_per_unit(tasks: List[HistoricalTask]) -> Tuple[float, float]:
    """
    Compute average cost per length unit and per complexity unit from historical data.

    Returns:
        (cost_per_length, cost_per_complexity)
    """
    if not tasks:
        # Fallback defaults when no history is available
        logger.debug("No historical tasks provided; using default cost factors.")
        return 0.001, 0.01

    total_len = sum(t.length for t in tasks)
    total_complex = sum(t.complexity for t in tasks)
    total_cost = sum(t.cost for t in tasks)

    # Weighted average: distribute total cost proportionally to length and complexity
    # Simple linear model: cost ≈ a*length + b*complexity
    # Solve least squares for a and b
    # For speed we use a heuristic: split cost proportionally.
    if total_len + total_complex == 0:
        return 0.0, 0.0

    # Proportion of cost attributable to length vs complexity
    len_ratio = total_len / (total_len + total_complex)
    comp_ratio = total_complex / (total_len + total_complex)

    cost_per_length = (total_cost * len_ratio) / total_len if total_len else 0.0
    cost_per_complexity = (total_cost * comp_ratio) / total_complex if total_complex else 0.0

    logger.debug(
        "Derived cost factors - per length: %.6f, per complexity: %.6f",
        cost_per_length, cost_per_complexity
    )
    return cost_per_length, cost_per_complexity


def predict_cost(
    task_length: int,
    complexity: float,
    similar_tasks: Optional[List[HistoricalTask]] = None,
) -> float:
    """
    Predict the cost of a new task.

    Parameters
    ----------
    task_length : int
        The size of the task (e.g., number of tokens, steps).
    complexity : float
        A user‑provided complexity score (higher means more demanding).
    similar_tasks : list[HistoricalTask] | None
        Historical records of similar tasks to base the prediction on.

    Returns
    -------
    float
        Estimated cost (arbitrary units; can be mapped to seconds, dollars, etc.).
    """
    if task_length < 0:
        raise ValueError("task_length must be non‑negative")
    if complexity < 0:
        raise ValueError("complexity must be non‑negative")

    cost_per_len, cost_per_comp = _average_cost_per_unit(similar_tasks or [])

    # Linear cost model
    estimated = task_length * cost_per_len + complexity * cost_per_comp

    # Guard against zero estimation when we have no history
    if estimated == 0.0:
        # Apply a minimal baseline cost
        estimated = max(task_length * 0.0005, complexity * 0.005, 0.01)

    logger.info(
        "Predicted cost: %.4f (length=%d, complexity=%.2f)",
        estimated, task_length, complexity
    )
    return estimated


# --------------------------------------------------------------------------- #
# Budget handling utilities
# --------------------------------------------------------------------------- #

class BudgetExceededWarning(UserWarning):
    """Raised when predicted cost exceeds the remaining budget."""


def check_budget(
    predicted_cost: float,
    remaining_budget: float,
    *,
    warn: bool = True,
    raise_error: bool = False,
) -> bool:
    """
    Evaluate whether a predicted cost fits within the remaining budget.

    Parameters
    ----------
    predicted_cost : float
        The cost predicted by ``predict_cost``.
    remaining_budget : float
        Available budget for the current session.
    warn : bool, default True
        Emit a ``BudgetExceededWarning`` if the cost exceeds the budget.
    raise_error : bool, default False
        If True, raise a ``RuntimeError`` instead of just warning.

    Returns
    -------
    bool
        ``True`` if the task can proceed (cost ≤ budget), ``False`` otherwise.
    """
    if predicted_cost <= remaining_budget:
        logger.debug(
            "Task within budget: predicted %.4f ≤ remaining %.4f",
            predicted_cost, remaining_budget,
        )
        return True

    message = (
        f"Predicted cost ({predicted_cost:.4f}) exceeds remaining budget "
        f"({remaining_budget:.4f})."
    )
    if warn:
        warnings.warn(message, BudgetExceededWarning)
        logger.warning(message)

    if raise_error:
        raise RuntimeError(message)

    return False


# --------------------------------------------------------------------------- #
# Convenience wrapper
# --------------------------------------------------------------------------- #

def can_execute_task(
    task_length: int,
    complexity: float,
    remaining_budget: float,
    similar_tasks: Optional[List[HistoricalTask]] = None,
) -> bool:
    """
    Shortcut that predicts cost and checks the budget in one call.

    Returns ``True`` if the task should be executed, ``False`` otherwise.
    """
    predicted = predict_cost(task_length, complexity, similar_tasks)
    return check_budget(predicted, remaining_budget)


# --------------------------------------------------------------------------- #
# Example usage (executed only when run as a script)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    # Simple demo with mock historical data
    history = [
        HistoricalTask(length=1000, complexity=2.0, cost=5.0),
        HistoricalTask(length=2000, complexity=3.5, cost=12.0),
        HistoricalTask(length=500,  complexity=1.0, cost=2.0),
    ]

    est = predict_cost(task_length=1500, complexity=2.5, similar_tasks=history)
    print(f"Estimated cost: {est:.4f}")

    budget = 10.0
    if can_execute_task(1500, 2.5, budget, history):
        print("Proceed with execution.")
    else:
        print("Skip – insufficient budget.")