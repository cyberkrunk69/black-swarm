"""
tool_router.py

Routes a tool request through a three‑stage hierarchy:

1. **Tool Store** – quick, free lookup of pre‑built tools.
2. **Component Assembler** – cheap assembly of existing components into a new tool.
3. **Full LLM Build** – expensive construction of a brand‑new LLM‑based tool and persistence.

The router uses a semantic search backend to match the incoming query to the most
relevant candidate at each stage.
"""

from typing import Any, Dict, Optional

# The following imports assume the experiment provides these helper modules.
# If they are not present, they should be added to the experiment package.
from .tool_store import find_tool_in_store
from .component_assembler import assemble_tool_from_components
from .llm_builder import build_and_store_llm_tool
from .semantic_search import semantic_match


def _search_stage(stage_name: str, query: str, candidates: list) -> Optional[Dict]:
    """
    Helper that runs semantic_match on a list of candidates and returns the best
    match if its similarity exceeds a stage‑specific threshold.

    Args:
        stage_name: Identifier for logging / debugging.
        query: User query / tool description.
        candidates: List of candidate dictionaries (each must contain a ``text`` key).

    Returns:
        The best matching candidate dict or ``None`` if no candidate passes the
        threshold.
    """
    if not candidates:
        return None

    # Perform semantic search; the function returns (best_candidate, score)
    best_candidate, score = semantic_match(query, candidates)

    # Define simple thresholds per stage (tunable)
    thresholds = {
        "store": 0.75,      # high confidence for free pre‑built tools
        "components": 0.60, # allow slightly looser matches for assembly
        "llm": 0.45,        # fall back to full build if nothing else fits
    }

    if score >= thresholds.get(stage_name, 0.5):
        return best_candidate
    return None


def route_tool_request(query: str) -> Any:
    """
    Main entry point. Routes ``query`` through the hierarchy and returns the
    resulting tool (or raises if all stages fail).

    Args:
        query: Natural‑language description of the desired tool.

    Returns:
        The instantiated tool object (type depends on the stage that succeeded).

    Raises:
        RuntimeError: If no stage can satisfy the request.
    """
    # ----------------------------------------------------------------------
    # 1️⃣  Check the free tool store
    # ----------------------------------------------------------------------
    store_candidates = find_tool_in_store(query, return_candidates=True)
    match = _search_stage("store", query, store_candidates)
    if match:
        # ``match`` contains enough info to retrieve the actual tool.
        return find_tool_in_store(match["id"])

    # ----------------------------------------------------------------------
    # 2️⃣  Try cheap component assembly
    # ----------------------------------------------------------------------
    component_candidates = assemble_tool_from_components(query, preview=True)
    # ``preview=True`` returns a list of possible assemblies without building.
    match = _search_stage("components", query, component_candidates)
    if match:
        # Build the selected assembly.
        return assemble_tool_from_components(match["spec"])

    # ----------------------------------------------------------------------
    # 3️⃣  Expensive full LLM build + persistence
    # ----------------------------------------------------------------------
    llm_candidates = build_and_store_llm_tool(query, preview=True)
    # ``preview=True`` yields candidate specs that could be built.
    match = _search_stage("llm", query, llm_candidates)
    if match:
        # Perform the full build and store the result.
        return build_and_store_llm_tool(match["spec"])

    # ----------------------------------------------------------------------
    # Nothing matched – raise an informative error.
    # ----------------------------------------------------------------------
    raise RuntimeError(
        f"Unable to satisfy tool request for: '{query}'. "
        "All hierarchy stages exhausted."
    )


# ----------------------------------------------------------------------
# Optional convenience wrapper for async environments
# ----------------------------------------------------------------------
async def async_route_tool_request(query: str) -> Any:
    """
    Async version of ``route_tool_request`` for compatibility with async
    frameworks. It simply runs the sync implementation in an executor.
    """
    import asyncio

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, route_tool_request, query)


# ----------------------------------------------------------------------
# Module self‑test (executed only when run directly)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    test_queries = [
        "summarize PDF documents",
        "translate English to French",
        "generate Python code from natural language description",
    ]

    for q in test_queries:
        try:
            tool = route_tool_request(q)
            print(f"[SUCCESS] Query: '{q}' → Tool: {tool}")
        except Exception as e:
            print(f"[FAIL] Query: '{q}' → {e}")