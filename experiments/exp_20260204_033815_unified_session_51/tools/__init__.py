"""
tools package initialization.

Provides a simple ToolRegistry that aggregates metadata from each tool submodule.
"""

from typing import Dict, Any


class ToolRegistry:
    """
    Registry for tool metadata.

    Each tool module should expose a ``TOOL_INFO`` dictionary with the following keys:
        - ``description``: Human‑readable semantic description.
        - ``input_schema``: JSON‑compatible schema describing expected inputs.
        - ``output_schema``: JSON‑compatible schema describing produced outputs.
        - ``usage_count``: Integer count of how many times the tool has been invoked.
        - ``success_rate``: Float between 0 and 1 indicating historic success.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, info: Dict[str, Any]) -> None:
        """Register a tool's metadata."""
        self._registry[name] = info

    def get(self, name: str) -> Dict[str, Any]:
        """Retrieve metadata for a given tool name."""
        return self._registry.get(name, {})

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return the full registry."""
        return self._registry


# Initialize the global registry and auto‑register known tools.
registry = ToolRegistry()

# Import tool submodules to pull in their TOOL_INFO.
from .filesystem import TOOL_INFO as FS_INFO
from .git import TOOL_INFO as GIT_INFO
from .testing import TOOL_INFO as TESTING_INFO
from .user_contributed import TOOL_INFO as USER_INFO

registry.register("filesystem", FS_INFO)
registry.register("git", GIT_INFO)
registry.register("testing", TESTING_INFO)
registry.register("user_contributed", USER_INFO)

__all__ = ["registry", "ToolRegistry"]