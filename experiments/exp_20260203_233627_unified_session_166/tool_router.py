import json
import os
import hashlib
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# ToolStore – a very lightweight persistent store for tools.
# ----------------------------------------------------------------------
class ToolStore:
    """
    Persists tools in a JSON file (tool_store.json).  Each entry has:
        - name: unique identifier (hash of description)
        - description: original task description
        - code: source code of the tool (string)
        - metadata: optional dict (e.g., author, created_at)
    """
    def __init__(self, store_path: str):
        self.store_path = store_path
        self._load_store()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_store(self) -> None:
        if os.path.exists(self.store_path):
            with open(self.store_path, "r", encoding="utf-8") as f:
                try:
                    self.store: Dict[str, Dict[str, Any]] = json.load(f)
                except json.JSONDecodeError:
                    self.store = {}
        else:
            self.store = {}
        # Ensure a dict for fast look‑ups
        if not isinstance(self.store, dict):
            self.store = {}

    def _save_store(self) -> None:
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(self.store, f, indent=2, ensure_ascii=False)

    def _hash_description(self, description: str) -> str:
        """Deterministic hash used as a stable key."""
        return hashlib.sha256(description.strip().lower().encode()).hexdigest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def lookup(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Return the stored tool dict if an exact match for the description exists,
        otherwise None.
        """
        key = self._hash_description(task_description)
        return self.store.get(key)

    def store_tool(self, tool_name: str, code: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Persist a new tool.  The key is derived from the tool_name (which should be
        unique per description).  If a tool with the same key already exists it is
        overwritten.
        """
        if metadata is None:
            metadata = {}
        key = self._hash_description(tool_name)
        self.store[key] = {
            "name": tool_name,
            "code": code,
            "metadata": metadata,
        }
        self._save_store()

    def compose(self, component_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Attempt to assemble a new tool from a list of component tool dicts.
        Very naive implementation: concatenate their code blocks.
        Returns a new tool dict or None if any component is missing.
        """
        if not component_list:
            return None
        # Verify all components are present
        for comp in component_list:
            if not comp or "code" not in comp:
                return None
        composed_code = "\n\n".join(comp["code"] for comp in component_list)
        composed_name = "composed_" + "_".join(comp["name"] for comp in component_list)
        return {
            "name": composed_name,
            "code": composed_code,
            "metadata": {"composed_from": [c["name"] for c in component_list]},
        }

# ----------------------------------------------------------------------
# LLM fallback stub – in real system this would call the LLM.
# ----------------------------------------------------------------------
def _generate_tool_via_llm(task_description: str) -> Dict[str, Any]:
    """
    Placeholder for LLM‑generated tool.  Returns a simple Python function that
    prints the description – replace with real LLM call.
    """
    safe_name = "".join(
        c if c.isalnum() else "_" for c in task_description.strip().lower()
    )[:50]
    code = f\"\"\"def {safe_name}():
    \"\"\"Auto‑generated stub for: {task_description}\"\"\"
    print("Executing auto‑generated tool for: {task_description}")
\"\"\"
    return {
        "name": safe_name,
        "code": code,
        "metadata": {"generated_by": "LLM_stub"},
    }

# ----------------------------------------------------------------------
# Router – orchestrates the lookup / compose / fallback flow.
# ----------------------------------------------------------------------
# Path where the JSON store lives – placed next to this file.
_DEFAULT_STORE_PATH = os.path.join(
    os.path.dirname(__file__), "tool_store.json"
)

_tool_store = ToolStore(_DEFAULT_STORE_PATH)

def route_task(task_description: str) -> Dict[str, Any]:
    """
    Main entry point used by the spawner (or any caller).

    1. Exact match lookup.
    2. Attempt composable lookup (components separated by '+').
    3. Fallback to LLM generation.
    4. Store the newly generated tool for future reuse.
    """
    # 1️⃣ Exact match
    exact = _tool_store.lookup(task_description)
    if exact:
        return exact

    # 2️⃣ Composable components (simple convention: "compA + compB")
    if "+" in task_description:
        components = [c.strip() for c in task_description.split("+")]
        comp_tools = [_tool_store.lookup(c) for c in components]
        if all(comp_tools):
            composed = _tool_store.compose(comp_tools)  # type: ignore[arg-type]
            if composed:
                # Store the composed tool for future exact matches
                _tool_store.store_tool(composed["name"], composed["code"], composed["metadata"])
                return composed

    # 3️⃣ LLM generation fallback
    generated = _generate_tool_via_llm(task_description)

    # 4️⃣ Persist the newly generated tool
    _tool_store.store_tool(generated["name"], generated["code"], generated["metadata"])
    return generated

# ----------------------------------------------------------------------
# Convenience wrapper for the spawner – mirrors existing project API.
# ----------------------------------------------------------------------
def get_tool(task_description: str) -> Dict[str, Any]:
    """
    Public API used by other modules (e.g., grind_spawner*.py) to obtain a tool.
    """
    return route_task(task_description)

# ----------------------------------------------------------------------
# If run as a script, demonstrate basic behaviour (optional, harmless).
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    desc = " ".join(sys.argv[1:]) or "example task"
    tool = get_tool(desc)
    print(f"Tool name: {tool['name']}")
    print("Code:")
    print(tool["code"])