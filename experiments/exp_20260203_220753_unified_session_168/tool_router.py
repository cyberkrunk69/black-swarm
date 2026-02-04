import os
import json
import types
from typing import Any, Callable, List, Optional, Dict

# ----------------------------------------------------------------------
# ToolStore: persistent JSON‑backed registry for generated tools
# ----------------------------------------------------------------------
class ToolStore:
    """
    Simple JSON‑based store for tool definitions.

    Each entry is keyed by a *task description* (str) and stores:
        - tool_name: identifier of the callable defined in the code
        - code:      source code defining the tool
        - metadata: arbitrary dict (e.g., version, author, components)
    """

    def __init__(self, store_path: str):
        self.store_path = store_path
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                self._store: Dict[str, Dict[str, Any]] = json.load(f)
        else:
            self._store = {}
            self._persist()  # create empty file

    def _persist(self) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self._store, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """Return the stored entry for an exact task description or None."""
        return self._store.get(task_description)

    def store(self, task_description: str, tool_name: str, code: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Persist a new tool definition."""
        if metadata is None:
            metadata = {}
        self._store[task_description] = {
            "tool_name": tool_name,
            "code": code,
            "metadata": metadata,
        }
        self._persist()

    def compose(self, component_list: List[str]) -> Optional[Dict[str, Any]]:
        """
        Assemble a new tool from previously stored components.

        component_list – list of *task descriptions* whose tools will be concatenated.
        Returns a dict with keys tool_name, code, metadata or None if any component is missing.
        """
        parts = []
        names = []
        for comp in component_list:
            entry = self._store.get(comp)
            if entry is None:
                return None
            names.append(entry["tool_name"])
            parts.append(entry["code"])

        assembled_code = "\n".join(parts)
        tool_name = "_".join(names)  # simple deterministic name
        metadata = {"components": component_list}
        return {"tool_name": tool_name, "code": assembled_code, "metadata": metadata}


# ----------------------------------------------------------------------
# Helper: turn source code string into a callable object
# ----------------------------------------------------------------------
def _load_callable_from_code(tool_name: str, code: str) -> Optional[Callable]:
    """
    Dynamically create a module from `code` and retrieve a callable named `tool_name`.
    Returns None if the callable cannot be found.
    """
    module = types.ModuleType(tool_name)
    try:
        exec(code, module.__dict__)
    except Exception as exc:
        # In a production system you would log this; keep it silent for now.
        return None
    return getattr(module, tool_name, None)


# ----------------------------------------------------------------------
# Global store instance (JSON lives alongside this file)
# ----------------------------------------------------------------------
_STORE_PATH = os.path.join(os.path.dirname(__file__), "tool_store.json")
tool_store = ToolStore(_STORE_PATH)


# ----------------------------------------------------------------------
# Router API
# ----------------------------------------------------------------------
def get_tool(
    task_description: str,
    component_list: Optional[List[str]] = None,
) -> Callable:
    """
    Resolve a tool for `task_description` following the hierarchy:

    1. Exact match in the store.
    2. Composition from `component_list` (if supplied).
    3. Fallback to LLM generation (currently NotImplementedError).

    On successful composition, the new tool is persisted for future look‑ups.
    """
    # 1️⃣ Exact match
    entry = tool_store.lookup(task_description)
    if entry:
        tool = _load_callable_from_code(entry["tool_name"], entry["code"])
        if tool:
            return tool

    # 2️⃣ Composable components
    if component_list:
        comp_entry = tool_store.compose(component_list)
        if comp_entry:
            tool = _load_callable_from_code(comp_entry["tool_name"], comp_entry["code"])
            if tool:
                # Cache the assembled tool under the original description
                tool_store.store(
                    task_description,
                    comp_entry["tool_name"],
                    comp_entry["code"],
                    comp_entry["metadata"],
                )
                return tool

    # 3️⃣ LLM fallback – placeholder
    raise NotImplementedError(
        "LLM generation fallback not implemented. "
        "Add your LLM integration here."
    )


def register_tool(
    task_description: str,
    tool_name: str,
    code: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Convenience wrapper to add a new tool to the store.
    """
    tool_store.store(task_description, tool_name, code, metadata)


# ----------------------------------------------------------------------
# Example integration stub with the existing spawner (read‑only core)
# ----------------------------------------------------------------------
# The core spawner expects a callable that performs the actual work.
# Users can replace their spawner calls with `spawn_with_tool` to enforce
# the tool‑first policy.

# from grind_spawner import spawn_task   # core spawner – read‑only

# def spawn_with_tool(task_description: str, *args, **kwargs):
#     """
#     Resolve a tool via the router and execute it instead of falling back
#     to the generic LLM path.
#     """
#     tool = get_tool(task_description)
#     return tool(*args, **kwargs)