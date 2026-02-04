"""
tools package initialization.

Provides a simple ToolRegistry for registering tool metadata such as
semantic description, input/output schema, usage count and success rate.
"""

from typing import Any, Dict, Optional


class ToolRegistry:
    """
    Central registry for all tools used in the experiment.

    Each entry is a mapping:
        {
            "description": str,
            "schema": Dict[str, Any],
            "usage_count": int,
            "success_rate": float  # 0.0 - 1.0
        }
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        schema: Dict[str, Any],
        usage_count: int = 0,
        success_rate: float = 0.0,
    ) -> None:
        """Register a new tool or update an existing one."""
        self._registry[name] = {
            "description": description,
            "schema": schema,
            "usage_count": usage_count,
            "success_rate": success_rate,
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve the metadata for a registered tool."""
        return self._registry.get(name)

    def increment_usage(self, name: str, success: bool) -> None:
        """Increment usage count and optionally update success rate."""
        tool = self._registry.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not registered.")
        tool["usage_count"] += 1
        # Update success rate using a simple running average
        total = tool["usage_count"]
        prev_rate = tool["success_rate"]
        tool["success_rate"] = ((prev_rate * (total - 1)) + (1.0 if success else 0.0)) / total

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of the full registry."""
        return dict(self._registry)


# Instantiate a global registry for convenience
registry = ToolRegistry()