import math
import json
from typing import Any, List, Optional, Tuple

# ----------------------------------------------------------------------
# Tree Node definition
# ----------------------------------------------------------------------
class TreeNode:
    """
    Represents a node in the LATS tree search.

    Attributes
    ----------
    state : Any
        The problem state represented by this node.
    action : Any
        The action taken to arrive at this state from its parent.
    parent : Optional[TreeNode]
        Reference to the parent node (None for root).
    children : List[TreeNode]
        List of child nodes.
    value : float
        Cumulative value (reward) obtained from simulations that passed through this node.
    visits : int
        Number of times this node has been visited/expanded.
    """

    def __init__(
        self,
        state: Any,
        action: Any = None,
        parent: Optional["TreeNode"] = None,
    ) -> None:
        self.state = state
        self.action = action
        self.parent = parent
        self.children: List["TreeNode"] = []
        self.value: float = 0.0
        self.visits: int = 0

    def is_fully_expanded(self) -> bool:
        """Placeholder – in a real implementation we would know the branching factor."""
        # For this generic stub we assume a node is fully expanded when it has at least one child.
        return len(self.children) > 0

    def best_child(self) -> Optional["TreeNode"]:
        """Return the child with the highest average value (exploitation only)."""
        if not self.children:
            return None
        return max(self.children, key=lambda c: (c.value / c.visits) if c.visits > 0 else float("-inf"))


# ----------------------------------------------------------------------
# Core LATS functions
# ----------------------------------------------------------------------
def expand_node(node: TreeNode, generate_children) -> None:
    """
    Expand a node by generating its child states.

    Parameters
    ----------
    node : TreeNode
        The node to expand.
    generate_children : Callable[[Any], List[Tuple[Any, Any]]]
        Function that, given a state, returns a list of (action, child_state) tuples.
    """
    if node.is_fully_expanded():
        return

    child_info = generate_children(node.state)
    for action, child_state in child_info:
        child_node = TreeNode(state=child_state, action=action, parent=node)
        node.children.append(child_node)


def evaluate_node(node: TreeNode, evaluate_state) -> float:
    """
    Evaluate a node's state and return a score in [0.0, 1.0].

    Parameters
    ----------
    node : TreeNode
        Node whose state should be evaluated.
    evaluate_state : Callable[[Any], float]
        Function that returns a quality score for a given state.

    Returns
    -------
    float
        The evaluation score.
    """
    score = evaluate_state(node.state)
    # Clamp to [0.0, 1.0] for safety.
    return max(0.0, min(1.0, score))


def ucb_score(child: TreeNode, parent_visits: int, exploration_constant: float = math.sqrt(2)) -> float:
    """
    Compute the Upper Confidence Bound (UCB) score for a child node.

    Parameters
    ----------
    child : TreeNode
        The child node.
    parent_visits : int
        Number of visits to the parent node.
    exploration_constant : float
        Exploration factor (default sqrt(2) as per classic UCT).

    Returns
    -------
    float
        The UCB score.
    """
    if child.visits == 0:
        # Encourage exploration of never‑visited nodes.
        return float("inf")
    exploitation = child.value / child.visits
    exploration = exploration_constant * math.sqrt(math.log(parent_visits) / child.visits)
    return exploitation + exploration


def select_best_child(node: TreeNode) -> Optional[TreeNode]:
    """
    Select the child with the highest UCB score.

    Parameters
    ----------
    node : TreeNode
        The node whose children are being considered.

    Returns
    -------
    Optional[TreeNode]
        The child with the highest UCB score, or None if there are no children.
    """
    if not node.children:
        return None
    parent_visits = max(node.visits, 1)  # avoid log(0)
    return max(node.children, key=lambda c: ucb_score(c, parent_visits))


def select_best_path(root: TreeNode) -> List[Any]:
    """
    Retrieve the best sequence of actions from the root to a leaf,
    based on average value (exploitation).

    Parameters
    ----------
    root : TreeNode
        The root of the search tree.

    Returns
    -------
    List[Any]
        Ordered list of actions leading to the best leaf.
    """
    path: List[Any] = []
    current = root
    while current.children:
        best = current.best_child()
        if best is None:
            break
        path.append(best.action)
        current = best
    return path


# ----------------------------------------------------------------------
# High‑level driver
# ----------------------------------------------------------------------
def run_tree_search(
    initial_state: Any,
    generate_children,
    evaluate_state,
    max_expansions: int = 10,
) -> Tuple[List[Any], TreeNode]:
    """
    Execute a simple LATS‑style tree search.

    Parameters
    ----------
    initial_state : Any
        Starting state of the problem.
    generate_children : Callable[[Any], List[Tuple[Any, Any]]]
        Function that returns possible (action, next_state) pairs for a given state.
    evaluate_state : Callable[[Any], float]
        Function that returns a quality score in [0, 1] for a given state.
    max_expansions : int, optional
        Maximum number of node expansions (default 10).

    Returns
    -------
    Tuple[List[Any], TreeNode]
        The best action path found and the root node of the constructed tree.
    """
    root = TreeNode(state=initial_state)

    for _ in range(max_expansions):
        # 1. Selection – descend using UCB.
        node = root
        while node.children:
            node = select_best_child(node)
            if node is None:
                break

        # 2. Expansion – generate children for the selected node.
        if node is not None:
            expand_node(node, generate_children)

        # 3. Simulation/Evaluation – evaluate each newly created child.
        if node is not None:
            for child in node.children:
                child.visits = 1
                child.value = evaluate_node(child, evaluate_state)

        # 4. Back‑propagation – update ancestors.
        while node is not None:
            node.visits += 1
            # Accumulate value from children (average of child values).
            if node.children:
                node.value = sum(c.value for c in node.children) / len(node.children)
            node = node.parent

    best_path = select_best_path(root)
    return best_path, root


# ----------------------------------------------------------------------
# Example placeholder utilities (to be replaced by the user)
# ----------------------------------------------------------------------
def _example_generate_children(state):
    """
    Dummy child generator – replace with domain‑specific logic.
    Returns a list of (action, new_state) tuples.
    """
    # For demonstration we create two dummy actions.
    return [("action_a", state + 1), ("action_b", state - 1)]


def _example_evaluate_state(state):
    """
    Dummy evaluator – replace with a real scoring function.
    Returns a float in [0, 1].
    """
    # Example: higher state value yields higher score (clamped).
    return max(0.0, min(1.0, state / 10.0))


if __name__ == "__main__":
    # Simple sanity check when the module is run directly.
    start = 5
    path, _ = run_tree_search(
        initial_state=start,
        generate_children=_example_generate_children,
        evaluate_state=_example_evaluate_state,
        max_expansions=20,
    )
    print("Best path found:", path)