"""
ToolRegistry – a lightweight registry for tools used in the unified session experiments.

Each tool module should expose a ``metadata`` dictionary with the following keys:
    - ``name``: Human readable name of the tool.
    - ``description``: Short semantic description.
    - ``input_schema``: JSON‑compatible description of expected input.
    - ``output_schema``: JSON‑compatible description of produced output.
    - ``usage_count``: Integer counter (starts at 0).
    - ``success_rate``: Float between 0.0 and 1.0 (starts at 0.0).

The registry loads all modules in the sibling sub‑packages (filesystem, git, testing,
user_contributed) and makes the metadata available via ``registry`` attribute.
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Any


class ToolRegistry:
    def __init__(self, base_package: str):
        """
        Initialise the registry.

        Parameters
        ----------
        base_package: str
            The dotted package path where tool sub‑modules live,
            e.g. ``experiments.exp_20260204_031218_unified_session_46.tools``.
        """
        self.base_package = base_package
        self.registry: Dict[str, Dict[str, Any]] = {}
        self._discover_tools()

    def _discover_tools(self):
        """Discover and import all sub‑modules that expose a ``metadata`` dict."""
        package = importlib.import_module(self.base_package)
        package_path = Path(package.__file__).parent

        for _, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
            if is_pkg:
                # Dive into sub‑package (e.g., filesystem, git, etc.)
                sub_pkg_path = package_path / module_name
                for _, sub_mod_name, _ in pkgutil.iter_modules([str(sub_pkg_path)]):
                    full_name = f"{self.base_package}.{module_name}.{sub_mod_name}"
                    self._register_module(full_name)
            else:
                # Direct module (unlikely in this layout)
                full_name = f"{self.base_package}.{module_name}"
                self._register_module(full_name)

    def _register_module(self, full_module_name: str):
        """Import a module and store its ``metadata`` if present."""
        try:
            mod = importlib.import_module(full_module_name)
            if hasattr(mod, "metadata"):
                meta = getattr(mod, "metadata")
                tool_key = meta.get("name", full_module_name)
                self.registry[tool_key] = meta
        except Exception as exc:
            # In a real system we would log this; for the experiment we silently ignore.
            pass

    def get_tool(self, name: str) -> Dict[str, Any]:
        """Retrieve metadata for a tool by its name."""
        return self.registry.get(name)

    def list_tools(self):
        """Return a list of registered tool names."""
        return list(self.registry.keys())


# Initialise a global registry instance for convenience.
# The package path is resolved relative to this file's location.
_global_pkg = __name__  # e.g. experiments.exp_20260204_031218_unified_session_46.tools
registry = ToolRegistry(_global_pkg)