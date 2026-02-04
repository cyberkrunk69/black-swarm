import json
import os
from typing import Any, Dict, List, Optional

# Path to the persistent tool store JSON file.
_TOOL_STORE_PATH = os.path.join(
    os.path.dirname(__file__), "tool_store.json"
)


class ToolStore:
    """
    Simple persistent store for tools.

    The JSON structure is a dict mapping tool names to a dict with keys:
        - "code": str  (the source code of the tool)
        - "metadata": dict (arbitrary metadata, must include at least "task_description")
        - "components": list[str] (optional list of component names used to compose the tool)
    """

    def __init__(self, store_path: str = _TOOL_STORE_PATH) -> None:
        self.store_path = store_path
        self._load_store()

    # --------------------------------------------------------------------- #
    # Persistence helpers
    # --------------------------------------------------------------------- #
    def _load_store(self) -> None:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self.store: Dict[str, Dict[str, Any]] = json.load(f)
            except Exception:
                # Corrupt file – start fresh
                self.store = {}
        else:
            self.store = {}

    def _dump_store(self) -> None:
        tmp_path = f"{self.store_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.store, f, indent=2, sort_keys=True)
        os.replace(tmp_path, self.store_path)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Return a stored tool whose metadata['task_description'] exactly matches
        the supplied description.  If no such tool exists, return None.
        """
        for tool_name, tool_data in self.store.items():
            meta = tool_data.get("metadata", {})
            if meta.get("task_description") == task_description:
                return {
                    "name": tool_name,
                    "code": tool_data["code"],
                    "metadata": meta,
                    "components": tool_data.get("components", []),
                }
        return None

    def store(self, tool_name: str, code: str, metadata: Dict[str, Any]) -> None:
        """
        Persist a new tool.  Overwrites any existing entry with the same name.
        """
        entry = {
            "code": code,
            "metadata": metadata,
            "components": metadata.get("components", []),
        }
        self.store[tool_name] = entry
        self._dump_store()

    def compose(self, component_list: List[str]) -> Optional[Dict[str, Any]]:
        """
        Assemble a new tool from previously stored components.

        The function concatenates the source code of each component in the order
        given and aggregates their metadata.  If any component is missing, None
        is returned.
        """
        assembled_code_parts = []
        aggregated_metadata: Dict[str, Any] = {"components": component_list}
        for comp_name in component_list:
            comp = self.store.get(comp_name)
            if not comp:
                # Missing component – cannot compose
                return None
            assembled_code_parts.append(comp["code"])
            # Merge simple metadata (non‑conflicting keys win the later component)
            comp_meta = comp.get("metadata", {})
            aggregated_metadata.update(comp_meta)

        assembled_code = "\n\n".join(assembled_code_parts)
        tool_name = "_".join(component_list)
        return {
            "name": tool_name,
            "code": assembled_code,
            "metadata": aggregated_metadata,
            "components": component_list,
        }


# ------------------------------------------------------------------------- #
# Router helper – integrates with the existing spawner (read‑only)
# ------------------------------------------------------------------------- #
def route_task(task_description: str, spawner: Any) -> Dict[str, Any]:
    """
    Resolve a task description to an executable tool.

    Steps:
      1. Exact match lookup in the ToolStore.
      2. Attempt to compose from known components (if the description encodes
         component names separated by '+', e.g. "compA+compB").
      3. Fall back to LLM generation via spawner.generate_tool().
      4. Store the newly generated tool for future reuse.

    Returns a dict with keys: name, code, metadata, components.
    """
    store = ToolStore()

    # 1️⃣ Exact match
    tool = store.lookup(task_description)
    if tool:
        return tool

    # 2️⃣ Composable components (simple convention: "comp1+comp2+comp3")
    if "+" in task_description:
        component_names = [c.strip() for c in task_description.split("+") if c.strip()]
        composed = store.compose(component_names)
        if composed:
            # Store the composed tool for future exact‑match lookups
            store.store(
                composed["name"],
                composed["code"],
                composed["metadata"],
            )
            return composed

    # 3️⃣ Fallback to LLM generation
    # The spawner is assumed to expose a `generate_tool` method that returns
    # a tuple (tool_name, code, metadata).  This contract is defined in the
    # core spawner implementation (read‑only).
    tool_name, code, metadata = spawner.generate_tool(task_description)

    # 4️⃣ Persist the newly generated tool
    store.store(tool_name, code, metadata)

    return {
        "name": tool_name,
        "code": code,
        "metadata": metadata,
        "components": metadata.get("components", []),
    }