"""
tool_router.py

Routes incoming tool requests through a three‑stage hierarchy:

1. **Tool Store (free)** – Look for an exact or semantically‑matched tool that is already
   materialised and can be returned without any extra cost.
2. **Component Assembly (cheap)** – If no ready‑made tool exists, try to compose one from
   available components (e.g., functions, prompts, models) that together satisfy the
   request.
3. **Full LLM Build + Store (expensive)** – As a last resort, trigger a full language‑model
   build, store the resulting artifact, and return it.

The module relies on a simple *semantic_search* utility to find the best match
within each collection. The actual stores / builders are assumed to live in sibling
modules; only the routing logic is implemented here.

Usage
-----
    from tool_router import ToolRouter

    router = ToolRouter()
    result = router.route(user_query)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# --------------------------------------------------------------------------- #
# Placeholder imports – replace with real implementations in the actual repo.
# --------------------------------------------------------------------------- #
try:
    from .tool_store import ToolStore  # Free, pre‑built tools
    from .component_store import ComponentStore  # Cheap, assemble‑able parts
    from .llm_builder import LLMBuilder  # Expensive full build
    from .semantic_search import semantic_search  # Generic semantic matcher
except Exception as e:  # pragma: no cover
    # If the real modules are missing (e.g., during CI sandbox), create minimal stubs.
    logging.warning(f"Import error in tool_router: {e}. Using fallback stubs.")

    class ToolStore:
        @staticmethod
        def search(query: str) -> Optional[Dict[str, Any]]:
            return None

    class ComponentStore:
        @staticmethod
        def search(query: str) -> Optional[Dict[str, Any]]:
            return None

        @staticmethod
        def assemble(components: Dict[str, Any]) -> Dict[str, Any]:
            return {"assembled": True, **components}

    class LLMBuilder:
        @staticmethod
        def build(query: str) -> Dict[str, Any]:
            return {"llm": "generated", "query": query}

    def semantic_search(query: str, collection: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Very naive fallback: return first item if collection not empty."""
        return collection[0] if collection else None

# --------------------------------------------------------------------------- #
# Core Router Implementation
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)


class ToolRouter:
    """
    Orchestrates the three‑step lookup/creation pipeline.
    """

    def __init__(self) -> None:
        self.tool_store = ToolStore()
        self.component_store = ComponentStore()
        self.llm_builder = LLMBuilder()

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def route(self, query: str) -> Dict[str, Any]:
        """
        Resolve a user request to a concrete tool.

        Parameters
        ----------
        query: str
            Natural‑language description of the desired tool.

        Returns
        -------
        dict
            A dictionary describing the resolved tool, together with metadata
            indicating which tier supplied it (``tier`` key: ``free``, ``cheap``,
            or ``expensive``).
        """
        logger.debug("Routing query through hierarchy: %s", query)

        # 1️⃣ Free tier – direct tool store lookup
        result = self._attempt_tool_store(query)
        if result:
            logger.info("Tool found in free store.")
            result["tier"] = "free"
            return result

        # 2️⃣ Cheap tier – component assembly
        result = self._attempt_component_assembly(query)
        if result:
            logger.info("Tool assembled from components (cheap tier).")
            result["tier"] = "cheap"
            return result

        # 3️⃣ Expensive tier – full LLM build
        result = self._attempt_full_build(query)
        logger.info("Tool built from scratch (expensive tier).")
        result["tier"] = "expensive"
        return result

    # ------------------------------------------------------------------- #
    # Tier implementations
    # ------------------------------------------------------------------- #
    def _attempt_tool_store(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search the free tool store using semantic similarity.
        """
        logger.debug("Searching free tool store.")
        # Assume ToolStore.search returns a list of candidate dicts.
        candidates = self.tool_store.search(query) or []
        match = semantic_search(query, candidates)
        if match:
            logger.debug("Free store match: %s", match.get("name"))
        return match

    def _attempt_component_assembly(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Find components that together satisfy the request and assemble them.
        """
        logger.debug("Searching component store.")
        candidates = self.component_store.search(query) or []
        match = semantic_search(query, candidates)
        if not match:
            logger.debug("No component match found.")
            return None

        logger.debug("Component match found: %s", match.get("id"))
        # The match may contain a list of component identifiers; we fetch them.
        component_ids = match.get("components", [])
        components = {}
        for cid in component_ids:
            # In a real implementation we'd retrieve each component; here we mock.
            comp = {"id": cid, "data": f"component_{cid}"}
            components[cid] = comp
            logger.debug("Fetched component %s", cid)

        assembled_tool = self.component_store.assemble(components)
        assembled_tool.update({"source_match": match})
        return assembled_tool

    def _attempt_full_build(self, query: str) -> Dict[str, Any]:
        """
        Trigger the expensive LLM building pipeline and store the result.
        """
        logger.debug("Invoking full LLM builder.")
        built_tool = self.llm_builder.build(query)

        # Persist the newly built tool back to the free store for future reuse.
        try:
            if hasattr(self.tool_store, "store"):
                self.tool_store.store(built_tool)  # type: ignore[attr-defined]
                logger.debug("Stored newly built tool in free store.")
        except Exception as e:  # pragma: no cover
            logger.warning(f"Failed to store built tool: {e}")

        return built_tool


# --------------------------------------------------------------------------- #
# Convenience singleton (optional)
# --------------------------------------------------------------------------- #
router = ToolRouter()

def route(query: str) -> Dict[str, Any]:
    """
    Shortcut function for the common case where only a single routing call is needed.
    """
    return router.route(query)