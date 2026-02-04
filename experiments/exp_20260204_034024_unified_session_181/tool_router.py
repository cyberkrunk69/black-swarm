"""
tool_router.py

Implements a “tool‑first” routing layer that prefers reusable tools over
generating new code with the LLM. The router works with a persistent
ToolStore (JSON‑backed) and provides a simple API:

    tool = route_task(task_description)

If a suitable tool is found or can be composed, it is returned; otherwise the
router falls back to a stub LLM generator, stores the newly created tool, and
returns it.

The design purposefully keeps the implementation lightweight and self‑contained
so that the core spawner can import and use it without any modifications to
read‑only system files.
"""

import json
import os
import threading
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# ToolStore – persistent JSON backed store
# --------------------------------------------------------------------------- #
class ToolStore:
    """
    Simple JSON‑backed store for tools.

    Structure of the JSON file (tool_store.json):
    {
        "tools": {
            "<tool_name>": {
                "code": "<source code>",
                "metadata": { ... }
            },
            ...
        }
    }
    """

    _lock = threading.Lock()

    def __init__(self, store_path: str):
        self.store_path = store_path
        # Ensure the file exists
        if not os.path.isfile(self.store_path):
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump({"tools": {}}, f, indent=2)

    # ----------------------------------------------------------------------- #
    # Internal helpers
    # ----------------------------------------------------------------------- #
    def _load_store(self) -> Dict[str, Any]:
        with open(self.store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_store(self, data: Dict[str, Any]) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ----------------------------------------------------------------------- #
    # Public API
    # ----------------------------------------------------------------------- #
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        1. Exact match – look for a tool whose name exactly matches the task.
        2. Component match – try to compose a tool from known components.
        Returns the tool dict (code + metadata) or None.
        """
        with self._lock:
            store = self._load_store()
            tools = store.get("tools", {})

            # Exact match
            if task_description in tools:
                return {"name": task_description, **tools[task_description]}

            # Component composition heuristic:
            # Split the description into words and see if any subset matches
            # known tool names. If we find at least two components we attempt
            # to assemble them.
            words = [w.strip().lower() for w in task_description.replace("_", " ").split()]
            component_names = [name for name in tools if name.lower() in words]

            if len(component_names) >= 2:
                composed = self.compose(component_names)
                if composed:
                    # Store the composed tool for future fast look‑ups
                    composed_name = "_".join(component_names)
                    self.store(composed_name, composed["code"], composed["metadata"])
                    return {"name": composed_name, **composed}

            # No suitable tool found
            return None

    def store(self, tool_name: str, code: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Persist a new tool. Overwrites any existing entry with the same name.
        """
        metadata = metadata or {}
        with self._lock:
            store = self._load_store()
            store.setdefault("tools", {})[tool_name] = {
                "code": code,
                "metadata": metadata,
            }
            self._save_store(store)

    def compose(self, component_list: List[str]) -> Optional[Dict[str, Any]]:
        """
        Assemble a new tool from existing components.
        Very naive implementation: concatenate the source code of each component
        in the order provided and merge metadata (later components win on key clash).
        Returns a dict with 'code' and 'metadata' or None if any component missing.
        """
        with self._lock:
            store = self._load_store()
            tools = store.get("tools", {})

            assembled_code_parts = []
            merged_metadata = {}

            for comp in component_list:
                comp_entry = tools.get(comp)
                if not comp_entry:
                    # Missing component – cannot compose
                    return None
                assembled_code_parts.append(f"# Component: {comp}\n{comp_entry['code']}\n")
                merged_metadata.update(comp_entry.get("metadata", {}))

            assembled_code = "\n".join(assembled_code_parts).strip()
            return {"code": assembled_code, "metadata": merged_metadata}


# --------------------------------------------------------------------------- #
# LLM stub – in a real system this would call the language model
# --------------------------------------------------------------------------- #
def _generate_tool_via_llm(task_description: str) -> Dict[str, Any]:
    """
    Placeholder for LLM generation. Returns a dummy tool that simply raises
    NotImplementedError when executed. In production replace this with the
    actual LLM call.
    """
    dummy_code = f\"\"\"def {task_description.replace(' ', '_')}(*args, **kwargs):
    raise NotImplementedError('Generated by LLM – replace with real implementation')
\"\"\"
    metadata = {"generated_by": "LLM", "task": task_description}
    return {"code": dummy_code, "metadata": metadata}


# --------------------------------------------------------------------------- #
# Public routing function
# --------------------------------------------------------------------------- #
def route_task(task_description: str,
               store_path: str = os.path.join(os.path.dirname(__file__), "tool_store.json")
               ) -> Dict[str, Any]:
    """
    Resolve a task to a concrete tool.

    1. Try exact lookup.
    2. Try composable components.
    3. Fallback to LLM generation.
    4. Store the newly generated tool for future reuse.

    Returns a dict:
        {
            "name": <tool_name>,
            "code": <source_code>,
            "metadata": {...}
        }
    """
    tool_store = ToolStore(store_path)

    # 1 & 2 – lookup (includes composition)
    tool = tool_store.lookup(task_description)
    if tool:
        return tool

    # 3 – fallback to LLM
    generated = _generate_tool_via_llm(task_description)

    # 4 – store for future use
    tool_name = task_description.replace(" ", "_")
    tool_store.store(tool_name, generated["code"], generated["metadata"])

    return {"name": tool_name, **generated}


# --------------------------------------------------------------------------- #
# Example usage (the spawner can import and call route_task)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple demo when run directly
    description = "example_task"
    result = route_task(description)
    print(f"Resolved tool: {result['name']}")
    print("Code:")
    print(result["code"])