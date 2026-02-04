# tools/__init__.py
"""
Tool Registry for the unified session experiment.

Each tool module should expose a `TOOL_INFO` dictionary with the following keys:
- name: Human‑readable name of the tool.
- description: Semantic description of what the tool does.
- input_schema: JSON‑compatible schema describing expected inputs.
- output_schema: JSON‑compatible schema describing outputs.
- usage_count: Number of times the tool has been invoked.
- success_rate: Float between 0 and 1 indicating historical success.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict] = {}
        self._load_tools()

    def _load_tools(self):
        """Dynamically discover and register tool modules under the tools package."""
        package_path = Path(__file__).parent
        for finder, name, ispkg in pkgutil.iter_modules([str(package_path)]):
            if ispkg:
                # Dive into sub‑packages (e.g., filesystem, git, testing, user_contributed)
                sub_pkg_path = package_path / name
                for sub_finder, sub_name, sub_ispkg in pkgutil.iter_modules([str(sub_pkg_path)]):
                    module_path = f"{__name__}.{name}.{sub_name}"
                    self._register_module(module_path)
            else:
                # Top‑level module (unlikely in this layout)
                module_path = f"{__name__}.{name}"
                self._register_module(module_path)

    def _register_module(self, module_path: str):
        try:
            module = importlib.import_module(module_path)
            tool_info = getattr(module, "TOOL_INFO", None)
            if tool_info and isinstance(tool_info, dict):
                tool_name = tool_info.get("name", module_path)
                self._tools[tool_name] = tool_info
        except Exception as e:
            # In a production system you might log this.
            pass

    def get_tool(self, name: str) -> Dict:
        """Retrieve tool metadata by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict]:
        """Return a list of all registered tool metadata dictionaries."""
        return list(self._tools.values())

    def increment_usage(self, name: str, success: bool):
        """Update usage count and success rate after an invocation."""
        tool = self._tools.get(name)
        if not tool:
            return
        tool["usage_count"] += 1
        # Recalculate success rate
        total = tool["usage_count"]
        prev_successes = tool["success_rate"] * (total - 1)
        tool["success_rate"] = (prev_successes + (1 if success else 0)) / total


# Instantiate a global registry for convenient import
registry = ToolRegistry()