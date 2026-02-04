import json
import os
from typing import Optional, Dict, Any, List

# Path to the persistent tool store (JSON file)
_TOOL_STORE_PATH = os.path.join(os.path.dirname(__file__), "tool_store.json")


class ToolStore:
    """
    Simple JSON‑backed store for tools.
    Each entry is keyed by a unique ``tool_name`` and contains:
        - ``code``: the Python source of the tool
        - ``metadata``: arbitrary dict (e.g., description, version)
        - ``components`` (optional): list of component tool names that can be composed
    """

    def __init__(self, store_path: str = _TOOL_STORE_PATH):
        self.store_path = store_path
        # Ensure the file exists
        if not os.path.isfile(self.store_path):
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

        # Load once; keep in memory for fast look‑ups
        self._load_store()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _load_store(self) -> None:
        with open(self.store_path, "r", encoding="utf-8") as f:
            self._store: Dict[str, Dict[str, Any]] = json.load(f)

    def _persist_store(self) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self._store, f, indent=2, sort_keys=True)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        1. Exact match: look for a tool whose ``metadata['description']`` exactly
           equals ``task_description``.
        2. Composable match: if no exact match, try to find a set of components
           whose combined description matches the request (very naive implementation).
        Returns the tool dict (including ``code``) or ``None`` if not found.
        """
        # Exact match
        for tool_name, entry in self._store.items():
            meta = entry.get("metadata", {})
            if meta.get("description") == task_description:
                return {"tool_name": tool_name, **entry}

        # Composable components (naïve – look for any tool that lists components)
        for tool_name, entry in self._store.items():
            components = entry.get("components")
            if not components:
                continue
            # Build a combined description from component metadata
            combined_desc = " ".join(
                self._store.get(comp, {}).get("metadata", {}).get("description", "")
                for comp in components
            )
            if task_description in combined_desc:
                # Assemble the tool on‑the‑fly
                assembled = self.compose(components)
                if assembled:
                    return {
                        "tool_name": f"{tool_name}_composed",
                        "code": assembled,
                        "metadata": {"description": task_description, "composed_from": components},
                    }

        # No match
        return None

    def store(self, tool_name: str, code: str, metadata: Dict[str, Any], components: List[str] = None) -> None:
        """
        Persist a new tool definition.
        """
        entry = {"code": code, "metadata": metadata}
        if components:
            entry["components"] = components
        self._store[tool_name] = entry
        self._persist_store()

    def compose(self, component_list: List[str]) -> Optional[str]:
        """
        Assemble a new tool by concatenating the ``code`` of the listed components.
        Returns the combined source code or ``None`` if any component is missing.
        """
        pieces = []
        for comp_name in component_list:
            comp = self._store.get(comp_name)
            if not comp:
                return None
            pieces.append(comp.get("code", ""))
        # Simple newline‑separated composition
        return "\n\n".join(pieces)


# --------------------------------------------------------------------- #
# Router convenience function (to be used by the spawner or other modules)
# --------------------------------------------------------------------- #
_tool_store = ToolStore()


def route_task(task_description: str) -> Dict[str, Any]:
    """
    Resolve a task description to a concrete tool.

    Returns a dict with at least:
        - ``tool_name``
        - ``code`` (source to exec)
        - ``metadata``
    If no tool is found, returns an empty dict signalling the caller to fall back
    to LLM generation.
    """
    result = _tool_store.lookup(task_description)
    return result or {}


# Example usage (can be removed in production):
if __name__ == "__main__":
    # Demonstrate storing a simple tool
    sample_code = """
def hello(name: str) -> str:
    return f"Hello, {name}!"
"""
    _tool_store.store(
        tool_name="greet_tool",
        code=sample_code,
        metadata={"description": "Say hello to a user", "version": "1.0"},
    )

    # Resolve it
    resolved = route_task("Say hello to a user")
    print("Resolved tool:", resolved.get("tool_name"))
    exec(resolved.get("code", ""), globals())
    print(hello("World"))