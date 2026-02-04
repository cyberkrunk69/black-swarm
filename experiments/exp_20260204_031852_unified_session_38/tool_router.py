"""
tool_router.py

Routes incoming tool requests through a three‑step hierarchy:

1. **Free tool store** – Look for an existing tool that satisfies the request.
2. **Component assembler** – If no exact tool exists, try to assemble one from cheap
   components.
3. **Full LLM build** – As a last resort, invoke the expensive LLM‑builder pipeline,
   then store the newly generated tool for future reuse.

The module uses a semantic search backend (``semantic_search``) to match the
natural‑language query against stored tools/components.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# ---- Placeholder imports ----------------------------------------------------
# In the actual code‑base these modules should provide the described APIs.
# They are imported lazily inside the functions to keep the router lightweight.
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------


def _semantic_match(query: str, candidates: list[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Perform a simple semantic match between ``query`` and a list of candidate
    dictionaries.  The function expects each candidate to have a ``'description'``
    field.  It returns the best‑matching candidate or ``None`` if no suitable match
    is found.

    The heavy lifting is delegated to ``semantic_search.search`` which returns a
    list of (candidate, score) tuples sorted by descending relevance.
    """
    try:
        from semantic_search import search  # type: ignore
    except Exception as exc:
        logger.error("Semantic search module unavailable: %s", exc)
        return None

    # Guard against empty candidate list
    if not candidates:
        return None

    # ``search`` returns list of (candidate, score) sorted by relevance.
    results = search(query, candidates, key="description")
    if not results:
        return None

    best_candidate, best_score = results[0]
    # Define a minimal relevance threshold (tunable)
    THRESHOLD = 0.6
    if best_score >= THRESHOLD:
        logger.debug("Semantic match found (score=%.2f): %s", best_score, best_candidate)
        return best_candidate
    logger.debug("No semantic match above threshold (best score=%.2f)", best_score)
    return None


# ---------------------------------------------------------------------------


def _try_tool_store(query: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to retrieve a ready‑made tool from the free tool store.
    """
    try:
        from tool_store import list_tools, get_tool_by_id  # type: ignore
    except Exception as exc:
        logger.error("Tool store module unavailable: %s", exc)
        return None

    tools = list_tools()  # Returns list of tool metadata dicts
    match = _semantic_match(query, tools)
    if match:
        tool_id = match["id"]
        logger.info("Tool found in free store: %s", tool_id)
        return get_tool_by_id(tool_id)
    logger.info("No matching tool in free store.")
    return None


# ---------------------------------------------------------------------------


def _try_component_assembly(query: str) -> Optional[Dict[str, Any]]:
    """
    Try to assemble a tool from cheap components.
    """
    try:
        from component_assembler import list_components, assemble_tool  # type: ignore
    except Exception as exc:
        logger.error("Component assembler module unavailable: %s", exc)
        return None

    components = list_components()
    match = _semantic_match(query, components)
    if not match:
        logger.info("No suitable component found for assembly.")
        return None

    # Attempt assembly; the assembler returns the assembled tool dict or None.
    assembled = assemble_tool(match["id"])
    if assembled:
        logger.info("Successfully assembled tool from component %s", match["id"])
    else:
        logger.warning("Component %s could not be assembled into a tool.", match["id"])
    return assembled


# ---------------------------------------------------------------------------


def _try_full_llm_build(query: str) -> Optional[Dict[str, Any]]:
    """
    As a last resort, build the tool using the expensive LLM pipeline and store it.
    """
    try:
        from llm_builder import build_tool  # type: ignore
        from tool_store import store_tool  # type: ignore
    except Exception as exc:
        logger.error("LLM builder or tool store module unavailable: %s", exc)
        return None

    logger.info("Invoking expensive LLM build for query: %s", query)
    built_tool = build_tool(query)  # Expected to return a tool dict
    if not built_tool:
        logger.error("LLM builder failed to produce a tool.")
        return None

    # Persist the newly built tool for future cheap retrieval.
    try:
        store_tool(built_tool)
        logger.info("Newly built tool stored with id %s", built_tool.get("id"))
    except Exception as exc:
        logger.warning("Storing built tool failed: %s", exc)

    return built_tool


# ---------------------------------------------------------------------------


def route_request(query: str) -> Optional[Dict[str, Any]]:
    """
    Public entry point.

    Parameters
    ----------
    query: str
        Natural‑language description of the desired tool.

    Returns
    -------
    dict or None
        The tool definition if one could be found/created, otherwise ``None``.
    """
    logger.info("Routing request: %s", query)

    # 1️⃣ Free tool store
    tool = _try_tool_store(query)
    if tool:
        return tool

    # 2️⃣ Cheap component assembly
    tool = _try_component_assembly(query)
    if tool:
        return tool

    # 3️⃣ Expensive full LLM build
    tool = _try_full_llm_build(query)
    return tool


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simple manual test harness
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tool_router.py '<natural language query>'")
        sys.exit(1)

    q = sys.argv[1]
    result = route_request(q)
    print(json.dumps(result, indent=2) if result else "No tool could be resolved.")