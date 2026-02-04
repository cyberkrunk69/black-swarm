# tools/__init__.py
"""
ToolRegistry provides a simple in‑memory registry for tool metadata.
Each tool module should expose a `metadata` dictionary with the following keys:
- name: str – human readable name
- description: str – semantic description of what the tool does
- input_schema: dict – JSON‑schema like description of expected inputs
- output_schema: dict – JSON‑schema like description of produced outputs
- usage_count: int – number of times the tool has been invoked
- success_rate: float – proportion of successful runs (0.0‑1.0)
"""

from typing import Dict, Any, List


class ToolRegistry:
    _registry: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, metadata: Dict[str, Any]) -> None:
        """Register a tool's metadata under a unique name."""
        cls._registry[name] = metadata

    @classmethod
    def get_tool(cls, name: str) -> Dict[str, Any]:
        """Retrieve metadata for a registered tool."""
        return cls._registry.get(name, {})

    @classmethod
    def list_tools(cls) -> List[str]:
        """Return a list of all registered tool names."""
        return list(cls._registry.keys())


# Auto‑register tools from sub‑packages when this package is imported.
def _auto_register():
    from .filesystem import metadata as fs_meta
    from .git import metadata as git_meta
    from .testing import metadata as testing_meta
    from .user_contributed import metadata as uc_meta

    ToolRegistry.register(fs_meta["name"], fs_meta)
    ToolRegistry.register(git_meta["name"], git_meta)
    ToolRegistry.register(testing_meta["name"], testing_meta)
    ToolRegistry.register(uc_meta["name"], uc_meta)


_auto_register()