"""
tool_router.py

Routes a tool request through a three‑step hierarchy:

1. **Free tool store** – look up an existing tool that matches the query.
2. **Component assembly** – if no exact tool exists, try to assemble one from
   cheaper components.
3. **Full LLM build** – as a last resort, trigger an expensive LLM build,
   store the result, and return it.

All look‑ups use a semantic‑search helper that returns similarity scores.
"""

from typing import Any, Dict, Optional

# The following imports are expected to exist in the repo.
# If they do not, they should be added to the experiment package.
from tool_store import find_tool_by_semantic_query   # free store
from component_store import find_components_for_query, assemble_tool_from_components  # cheap
from llm_builder import build_tool_from_llm, store_built_tool  # expensive
from semantic_search import semantic_similarity  # generic similarity helper


def _select_best_candidate(candidates: list[Dict[str, Any]], threshold: float = 0.75) -> Optional[Dict[str, Any]]:
    """
    Return the candidate with the highest similarity score above ``threshold``.
    Each candidate dict must contain a ``'score'`` key.
    """
    if not candidates:
        return None
    # Sort descending by score
    candidates = sorted(candidates, key=lambda c: c['score'], reverse=True)
    best = candidates[0]
    return best if best['score'] >= threshold else None


def route_request(query: str) -> Any:
    """
    Resolve a tool request.

    Parameters
    ----------
    query: str
        Natural‑language description of the desired tool.

    Returns
    -------
    Any
        The resolved tool object (could be a stored tool, an assembled one,
        or a freshly built LLM tool).
    """
    # ------------------------------------------------------------------
    # 1️⃣  Check the free tool store
    # ------------------------------------------------------------------
    free_candidates = find_tool_by_semantic_query(query)
    best_free = _select_best_candidate(free_candidates, threshold=0.80)
    if best_free:
        return best_free['tool']

    # ------------------------------------------------------------------
    # 2️⃣  Try to assemble from cheap components
    # ------------------------------------------------------------------
    component_candidates = find_components_for_query(query)
    best_components = _select_best_candidate(component_candidates, threshold=0.70)
    if best_components:
        # ``components`` is expected to be a list of component objects.
        assembled = assemble_tool_from_components(best_components['components'])
        if assembled:
            # Optionally cache the assembled tool for future free look‑ups.
            store_built_tool(assembled, free=True)
            return assembled

    # ------------------------------------------------------------------
    # 3️⃣  Expensive full LLM build + store
    # ------------------------------------------------------------------
    # Build the tool using the LLM, then persist it for future requests.
    built_tool = build_tool_from_llm(query)
    if built_tool:
        store_built_tool(built_tool, free=False)  # mark as expensive‑origin
        return built_tool

    # If everything fails, raise a clear error.
    raise RuntimeError(f"Unable to resolve tool for query: {query!r}")


# ----------------------------------------------------------------------
# Convenience wrapper for external callers (e.g., API endpoints)
# ----------------------------------------------------------------------
def handle_tool_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected payload format:
        { "query": "<natural language description>" }

    Returns a JSON‑serialisable dict with either the tool data or an error.
    """
    query = payload.get("query", "").strip()
    if not query:
        return {"error": "Missing 'query' field in request payload."}

    try:
        tool = route_request(query)
        # Assume each tool object implements ``to_dict`` for serialization.
        return {"tool": tool.to_dict() if hasattr(tool, "to_dict") else str(tool)}
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}


if __name__ == "__main__":
    # Simple manual test harness
    import json, sys
    if len(sys.argv) < 2:
        print("Usage: python tool_router.py '<query>'")
        sys.exit(1)

    q = sys.argv[1]
    result = handle_tool_request({"query": q})
    print(json.dumps(result, indent=2))