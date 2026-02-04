"""
tool_router.py

Implements the **ToolRouter** – a hierarchical selector that chooses the most
appropriate tool (callable) based on a cost tier ordering:
free → cheap → expensive.

The router is configurable at runtime:
* Register tools under a tier.
* Query the router for a tool that satisfies a predicate; the router walks the
  hierarchy from cheapest to most expensive until a match is found.

The implementation is deliberately simple, type‑annotated, and includes a
fallback mechanism that raises a clear error if no tool matches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple, TypeVar

T = TypeVar("T")


@dataclass
class ToolSpec:
    """
    Wrapper for a tool callable.

    Attributes
    ----------
    name: str
        Identifier used for debugging / logging.
    func: Callable[..., T]
        The actual executable.
    """
    name: str
    func: Callable[..., T]


class ToolRouter:
    """
    Hierarchical selector for tools.

    Tier ordering (cheapest first):
    0 – free
    1 – cheap
    2 – expensive
    """

    _tier_order = ["free", "cheap", "expensive"]

    def __init__(self) -> None:
        # Mapping tier -> list of ToolSpec
        self._registry: Dict[str, List[ToolSpec]] = {tier: [] for tier in self._tier_order}

    # --------------------------------------------------------------------- #
    # Registration
    # --------------------------------------------------------------------- #
    def register(self, tier: str, tool: ToolSpec) -> None:
        """
        Register ``tool`` under ``tier``. ``tier`` must be one of the predefined
        strings; otherwise a ``ValueError`` is raised.
        """
        if tier not in self._tier_order:
            raise ValueError(f"Invalid tier '{tier}'. Valid tiers: {self._tier_order}")
        self._registry[tier].append(tool)

    # --------------------------------------------------------------------- #
    # Retrieval
    # --------------------------------------------------------------------- #
    def get_tool(self, predicate: Callable[[ToolSpec], bool]) -> ToolSpec:
        """
        Return the first tool (according to tier priority) whose ``predicate``
        returns ``True``. If none match, raise ``LookupError``.
        """
        for tier in self._tier_order:
            for tool in self._registry[tier]:
                if predicate(tool):
                    return tool
        raise LookupError("No tool satisfies the given predicate in any tier")

    # --------------------------------------------------------------------- #
    # Convenience shortcut – direct call
    # --------------------------------------------------------------------- #
    def __call__(self, *args, **kwargs) -> T:
        """
        Shortcut for ``self.get_tool(lambda t: True).func(*args, **kwargs)``.
        Returns the cheapest available tool regardless of any predicate.
        """
        tool = self.get_tool(lambda _: True)
        return tool.func(*args, **kwargs)

    # --------------------------------------------------------------------- #
    # Inspection helpers
    # --------------------------------------------------------------------- #
    def list_tools(self) -> List[Tuple[str, str]]:
        """
        Return a flat list of ``(tier, tool_name)`` tuples for debugging.
        """
        return [(tier, tool.name) for tier in self._tier_order for tool in self._registry[tier]]