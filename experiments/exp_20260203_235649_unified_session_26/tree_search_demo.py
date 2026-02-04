"""
tree_search_demo.py

A minimal demonstration of a Latent Action Tree Search (LATS) style planner.
The implementation is intentionally lightweight: it builds a simple tree of
possible actions, evaluates them with a heuristic, and returns the best
action sequence.

This demo is self‑contained and does not require any external libraries
beyond the Python standard library.
"""

from __future__ import annotations
from typing import List, Tuple, Callable, Any
import heapq


class Node:
    """A node in the search tree."""
    def __init__(self, state: Any, path: List[Any], cost: float):
        self.state = state          # current state representation
        self.path = path            # actions taken to reach this state
        self.cost = cost            # cumulative cost (lower is better)

    def __lt__(self, other: "Node"):
        # Required for heapq to compare nodes by cost
        return self.cost < other.cost


def simple_transition(state: int, action: int) -> int:
    """
    Dummy transition function.
    State is an integer; action adds or subtracts a value.
    """
    return state + action


def heuristic(state: int, goal: int) -> float:
    """Straight‑line distance to the goal."""
    return abs(goal - state)


def lats_plan(
    start: int,
    goal: int,
    actions: List[int],
    max_depth: int = 5,
    branching_factor: int = 3,
) -> Tuple[List[int], float]:
    """
    Perform a very small‑scale Latent Action Tree Search.

    Args:
        start: initial integer state.
        goal: integer goal state.
        actions: list of possible integer actions (e.g., [+1, -1, +2]).
        max_depth: maximum depth of the search tree.
        branching_factor: limit of actions explored per node (for demo).

    Returns:
        (best_path, best_cost) where best_path is a list of actions.
    """
    # Priority queue ordered by f = g + h
    frontier: List[Tuple[float, Node]] = []
    start_node = Node(state=start, path=[], cost=0.0)
    heapq.heappush(frontier, (heuristic(start, goal), start_node))

    best_solution: Tuple[List[int], float] = ([], float("inf"))

    while frontier:
        _, current = heapq.heappop(frontier)

        # Goal test
        if current.state == goal:
            if current.cost < best_solution[1]:
                best_solution = (current.path, current.cost)
            continue

        if len(current.path) >= max_depth:
            continue

        # Expand node (limit branching for demo)
        for action in actions[:branching_factor]:
            next_state = simple_transition(current.state, action)
            step_cost = 1.0  # uniform step cost for demo
            g = current.cost + step_cost
            h = heuristic(next_state, goal)
            f = g + h
            child = Node(state=next_state, path=current.path + [action], cost=g)
            heapq.heappush(frontier, (f, child))

    return best_solution


if __name__ == "__main__":
    # Demo run
    start_state = 0
    goal_state = 7
    possible_actions = [1, -1, 2, -2, 3]

    plan, cost = lats_plan(start_state, goal_state, possible_actions, max_depth=6)
    print(f"Best plan from {start_state} to {goal_state}: {plan} (cost={cost})")