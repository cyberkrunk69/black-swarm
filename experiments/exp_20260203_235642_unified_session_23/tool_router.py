"""
ToolRouter – Hierarchical tool selection based on cost tiers.

The router maintains three cost tiers:

* ``free``   – zero‑cost utilities.
* ``cheap``  – low‑cost, possibly rate‑limited services.
* ``expensive`` – high‑cost, high‑quality services.

When a task is routed, the router attempts to find a capable tool in the
cheapest tier first, falling back to more expensive tiers only if needed.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List, Tuple


class ToolRouter:
    """
    Registers tools under cost categories and selects the cheapest capable
    tool for a given task.
    """

    def __init__(self):
        # cost_category -> list of (name, can_handle, executor)
        self._registry: Dict[str, List[Tuple[str, Callable[[Any], bool], Callable[[Any], Any]]]] = defaultdict(list)
        self._tier_order = ["free", "cheap", "expensive"]

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def register_tool(
        self,
        name: str,
        cost_category: str,
        can_handle: Callable[[Any], bool],
        executor: Callable[[Any], Any],
    ) -> None:
        """
        Register a tool.

        Parameters
        ----------
        name: str
            Human‑readable identifier.
        cost_category: str
            One of ``free``, ``cheap``, ``expensive``.
        can_handle: Callable[[Any], bool]
            Predicate that returns True if the tool can process the supplied task.
        executor: Callable[[Any], Any]
            Function that actually performs the work.
        """
        if cost_category not in self._tier_order:
            raise ValueError(f"Invalid cost_category '{cost_category}'.")
        self._registry[cost_category].append((name, can_handle, executor))

    def route(self, task: Any) -> Any:
        """
        Find the cheapest capable tool and execute the task.

        Returns
        -------
        Any
            The result returned by the selected tool's executor.
        """
        for tier in self._tier_order:
            for name, can_handle, executor in self._registry[tier]:
                if can_handle(task):
                    return executor(task)
        raise RuntimeError("No suitable tool found for the given task.")