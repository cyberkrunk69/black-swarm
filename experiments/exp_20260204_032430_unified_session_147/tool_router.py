import json
import os
import threading
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# ToolStore – persistent JSON backed store for tools and composable parts
# ----------------------------------------------------------------------
class ToolStore:
    """
    Simple JSON‑backed store that holds:
      - exact tools keyed by a textual description
      - reusable components that can be assembled into new tools
    The store is thread‑safe for the simple read‑modify‑write pattern used
    throughout the router.
    """
    _lock = threading.Lock()

    def __init__(self, store_path: Optional[str] = None):
        # Default location is alongside this file in the experiment folder
        if store_path is None:
            base_dir = os.path.dirname(__file__)
            store_path = os.path.join(base_dir, "tool_store.json")
        self.store_path = store_path
        self._ensure_store_file()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_store_file(self) -> None:
        """Create an empty JSON file if it does not exist."""
        if not os.path.exists(self.store_path):
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump({"tools": {}, "components": {}}, f, indent=2)

    def _load_store(self) -> Dict[str, Any]:
        with open(self.store_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_store(self, data: Dict[str, Any]) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Return a stored tool that exactly matches the given description.
        If none is found, return None.
        """
        with self._lock:
            store = self._load_store()
            return store["tools"].get(task_description)

    def store(self, tool_name: str, code: str, metadata: Dict[str, Any]) -> None:
        """
        Persist a new tool. The key is the human readable description
        supplied in metadata['description'].
        """
        description = metadata.get("description")
        if not description:
            raise ValueError("Metadata must contain a 'description' field for lookup.")
        tool_entry = {
            "name": tool_name,
            "code": code,
            "metadata": metadata,
        }
        with self._lock:
            store = self._load_store()
            store["tools"][description] = tool_entry
            self._write_store(store)

    def add_component(self, component_name: str, code: str, metadata: Dict[str, Any]) -> None:
        """
        Store a reusable component that can later be composed.
        """
        comp_entry = {
            "name": component_name,
            "code": code,
            "metadata": metadata,
        }
        with self._lock:
            store = self._load_store()
            store["components"][component_name] = comp_entry
            self._write_store(store)

    def compose(self, component_list: List[str]) -> Optional[Dict[str, Any]]:
        """
        Assemble a new tool from a list of component names.
        Returns a dict with combined code and aggregated metadata,
        or None if any component is missing.
        """
        with self._lock:
            store = self._load_store()
            components = store["components"]
            missing = [c for c in component_list if c not in components]
            if missing:
                return None

            # Simple concatenation of code snippets; more sophisticated logic can be added.
            assembled_code = "\n".join(components[c]["code"] for c in component_list)
            aggregated_metadata = {
                "components": component_list,
                "generated_by": "ToolStore.compose",
            }
            return {
                "name": "_".join(component_list) + "_assembled",
                "code": assembled_code,
                "metadata": aggregated_metadata,
            }

# ----------------------------------------------------------------------
# Router – orchestrates lookup, composition, and LLM fallback
# ----------------------------------------------------------------------
def get_tool(
    task_description: str,
    llm_generate_func,
    component_hint: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Resolve a tool for the supplied description using the hierarchy:
      1. Exact match in the store
      2. Composition from known components (if hints supplied)
      3. LLM generation as last resort
    After successful execution of a generated tool, it is stored for future reuse.
    """
    store = ToolStore()

    # 1️⃣ Exact match
    tool = store.lookup(task_description)
    if tool:
        return tool

    # 2️⃣ Try composable components if a hint list is provided
    if component_hint:
        composed = store.compose(component_hint)
        if composed:
            # Store the newly composed tool under the original description for fast future hits
            store.store(
                tool_name=composed["name"],
                code=composed["code"],
                metadata={**composed["metadata"], "description": task_description},
            )
            return composed

    # 3️⃣ LLM fallback – user supplies a callable that returns a dict with
    #    {name, code, metadata}. The metadata must include a 'description' key.
    generated = llm_generate_func(task_description)
    if not isinstance(generated, dict) or "code" not in generated:
        raise RuntimeError("LLM generation did not return a valid tool dict.")

    # 4️⃣ Persist the newly created tool for future calls
    description = generated.get("metadata", {}).get("description", task_description)
    store.store(
        tool_name=generated.get("name", "generated_tool"),
        code=generated["code"],
        metadata={**generated.get("metadata", {}), "description": description},
    )
    return generated

# ----------------------------------------------------------------------
# Example integration point for the existing spawner (read‑only core)
# ----------------------------------------------------------------------
# The core spawner expects a callable named `resolve_tool` in the module
# path it receives. By exposing `resolve_tool` we let the spawner request a
# tool without any modifications to its own source.
def resolve_tool(task_description: str, llm_generate_func, component_hint: Optional[List[str]] = None):
    """
    Wrapper used by the spawner to obtain a ready‑to‑execute tool.
    """
    return get_tool(task_description, llm_generate_func, component_hint)