import math
import random
import json
from typing import Any, List, Optional, Tuple

# ----------------------------------------------------------------------
# Tree Search implementation inspired by LATS (arXiv:2310.04406)
# ----------------------------------------------------------------------


class TreeNode:
    """
    Represents a node in the search tree.

    Attributes
    ----------
    state : Any
        The problem state represented by this node.
    action : Any
        The action taken to reach this node from its parent (None for root).
    parent : Optional[TreeNode]
        Reference to the parent node.
    children : List[TreeNode]
        List of child nodes.
    value : float
        Accumulated value (reward) of the node.
    visits : int
        Number of times the node has been visited.
    """

    def __init__(self, state: Any, action: Any = None, parent: Optional["TreeNode"] = None):
        self.state = state
        self.action = action
        self.parent = parent
        self.children: List["TreeNode"] = []
        self.value: float = 0.0
        self.visits: int = 0

    def is_fully_expanded(self) -> bool:
        """Placeholder: in a real implementation this would check if all possible
        actions from ``state`` have been generated."""
        return len(self.children) > 0

    def __repr__(self) -> str:
        return (
            f"TreeNode(state={self.state!r}, action={self.action!r}, "
            f"value={self.value:.3f}, visits={self.visits})"
        )


# ----------------------------------------------------------------------
# Core functions
# ----------------------------------------------------------------------


def expand_node(node: TreeNode) -> List[TreeNode]:
    """
    Generate child nodes for ``node``.

    For demonstration purposes we create deterministic dummy children.
    If ``node.state`` is an integer we generate ``state + 1`` and ``state + 2``.
    Otherwise we create a single child with a modified representation.

    Returns
    -------
    List[TreeNode]
        The newly created child nodes.
    """
    if isinstance(node.state, int):
        child_states = [node.state + 1, node.state + 2]
    elif isinstance(node.state, (list, tuple)):
        # Append a new element to the list/tuple
        child_states = [node.state + (i,) for i in range(2)]
    else:
        # Fallback: create a single dummy child
        child_states = [f"{node.state}_c{i}" for i in range(2)]

    children = []
    for idx, st in enumerate(child_states):
        child = TreeNode(state=st, action=idx, parent=node)
        children.append(child)

    node.children.extend(children)
    return children


def evaluate_node(node: TreeNode) -> float:
    """
    Evaluate ``node`` and return a score in the range [0.0, 1.0].

    This stub uses a random uniform value; in a real system this would call a
    domain‑specific evaluator (e.g., a neural model or heuristic).

    The score is also stored in ``node.value`` for later aggregation.
    """
    score = random.random()
    node.value = score
    return score


def ucb_score(child: TreeNode, parent_visits: int, exploration_constant: float = math.sqrt(2)) -> float:
    """
    Compute the Upper Confidence Bound (UCB) score for a child node.

    Parameters
    ----------
    child : TreeNode
        The child node.
    parent_visits : int
        Number of visits of the parent node.
    exploration_constant : float
        The constant controlling exploration (default sqrt(2)).

    Returns
    -------
    float
        The UCB score. Unvisited nodes receive ``inf`` to guarantee selection.
    """
    if child.visits == 0:
        return float("inf")
    exploitation = child.value / child.visits
    exploration = exploration_constant * math.sqrt(math.log(parent_visits) / child.visits)
    return exploitation + exploration


def select_promising_node(root: TreeNode) -> TreeNode:
    """
    Starting from ``root``, descend the tree by repeatedly selecting the child
    with the highest UCB score until a leaf (node without children) is reached.

    Returns
    -------
    TreeNode
        The leaf node selected for expansion.
    """
    node = root
    while node.children:
        scores = [
            ucb_score(child, node.visits) for child in node.children
        ]
        max_index = scores.index(max(scores))
        node = node.children[max_index]
    return node


def backpropagate(node: TreeNode, reward: float) -> None:
    """
    Propagate ``reward`` up the tree, updating ``visits`` and ``value`` for each
    ancestor (including ``node`` itself).
    """
    while node is not None:
        node.visits += 1
        node.value += reward
        node = node.parent


def select_best_path(root: TreeNode) -> List[Any]:
    """
    Retrieve the best sequence of actions from ``root`` to a leaf by always
    following the child with the highest average value (value / visits).

    Returns
    -------
    List[Any]
        List of actions representing the best discovered path.
    """
    path: List[Any] = []
    node = root
    while node.children:
        # Choose child with highest average value
        best_child = max(
            node.children,
            key=lambda c: (c.value / c.visits) if c.visits > 0 else -float("inf"),
        )
        path.append(best_child.action)
        node = best_child
    return path


def run_tree_search(initial_state: Any, max_expansions: int = 10) -> Tuple[List[Any], TreeNode]:
    """
    Perform a simple LATS‑style tree search.

    Parameters
    ----------
    initial_state : Any
        The starting state for the search.
    max_expansions : int
        Maximum number of node expansions.

    Returns
    -------
    Tuple[List[Any], TreeNode]
        A tuple containing the best action path and the root node of the tree.
    """
    root = TreeNode(state=initial_state)

    # Initial evaluation of the root
    root_reward = evaluate_node(root)
    backpropagate(root, root_reward)

    for _ in range(max_expansions):
        # 1. Selection – pick a leaf to expand
        leaf = select_promising_node(root)

        # 2. Expansion – generate children
        children = expand_node(leaf)
        if not children:
            # No possible expansions; treat leaf as terminal
            continue

        # 3. Evaluation – evaluate each new child
        for child in children:
            reward = evaluate_node(child)
            backpropagate(child, reward)

    best_path = select_best_path(root)
    return best_path, root


# ----------------------------------------------------------------------
# Example usage (can be removed or guarded by __main__)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    start_state = 0
    path, tree_root = run_tree_search(start_state, max_expansions=20)
    print("Best path of actions:", path)
    print("Root node after search:", tree_root)