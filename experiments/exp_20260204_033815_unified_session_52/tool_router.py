"""
tool_router.py

Routes tool acquisition/build requests through a three‑tier hierarchy:

1️⃣ **Free Tool Store** – Look up an existing tool in the cached store.
2️⃣ **Cheap Component Assembly** – If not found, try to assemble the tool from
   inexpensive components.
3️⃣ **Expensive Full LLM Build** – As a last resort, invoke the LLM builder,
   then persist the newly created tool.

The router relies on a simple semantic‑search helper that matches a textual
request to stored entries.  All heavy‑weight operations are deferred until the
previous tier fails, keeping costs low for the common case.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# Local imports – these modules are expected to exist in the same experiment
# package.  Import errors will surface early during testing.
try:
    from .tool_store import get_tool_by_semantic_query, store_tool
    from .component_assembler import assemble_tool_from_components, cheap_component_catalog
    from .llm_builder import build_tool_with_llm, expensive_tool_store
except ImportError as exc:
    # If any of the expected modules are missing, raise a clear error.
    raise ImportError(f"tool_router initialization failed: {exc}") from exc

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _semantic_search(query: str, candidates: Dict[str, Any]) -> Optional[str]:
    """
    Very lightweight semantic‑search stub.

    Parameters
    ----------
    query: str
        The user request (e.g., "translate English to French").
    candidates: dict
        Mapping of candidate identifiers to their metadata (must contain a
        ``'description'`` key).

    Returns
    -------
    Optional[str]
        The identifier of the best‑matching candidate, or ``None`` if no
        suitable match is found.
    """
    # In a real system this would call an embedding model + similarity metric.
    # Here we perform a naive case‑insensitive substring match as a placeholder.
    lowered = query.lower()
    for tool_id, meta in candidates.items():
        desc = meta.get("description", "").lower()
        if lowered in desc or desc in lowered:
            return tool_id
    return None


def route_tool_request(request: str, **kwargs: Any) -> Any:
    """
    Resolve a tool request using the three‑tier strategy.

    Parameters
    ----------
    request: str
        Natural‑language description of the desired tool.
    **kwargs:
        Additional arguments forwarded to the underlying builders/assemblers
        (e.g., temperature, max_tokens).

    Returns
    -------
    Any
        The retrieved or newly created tool object.

    Raises
    ------
    RuntimeError
        If all three tiers fail to produce a tool.
    """
    logger.info("Routing tool request: %s", request)

    # ------------------------------------------------------------------
    # 1️⃣  Free Tool Store
    # ------------------------------------------------------------------
    logger.debug("Attempting free‑tool lookup.")
    free_candidates = get_tool_by_semantic_query(request, store="free")
    if free_candidates:
        tool_id = _semantic_search(request, free_candidates)
        if tool_id:
            logger.info("Found tool in free store: %s", tool_id)
            return free_candidates[tool_id]["instance"]

    # ------------------------------------------------------------------
    # 2️⃣  Cheap Component Assembly
    # ------------------------------------------------------------------
    logger.debug("Free lookup failed – trying cheap component assembly.")
    component_candidates = cheap_component_catalog()
    comp_match_id = _semantic_search(request, component_candidates)
    if comp_match_id:
        logger.info("Assembling tool from cheap components: %s", comp_match_id)
        assembled_tool = assemble_tool_from_components(comp_match_id, **kwargs)
        # Store the assembled tool for future free look‑ups.
        store_tool(assembled_tool, tier="free")
        return assembled_tool

    # ------------------------------------------------------------------
    # 3️⃣  Expensive Full LLM Build
    # ------------------------------------------------------------------
    logger.debug("Component assembly failed – invoking full LLM build.")
    llm_candidates = expensive_tool_store()
    llm_match_id = _semantic_search(request, llm_candidates)
    if llm_match_id:
        logger.info("Building tool with LLM: %s", llm_match_id)
        built_tool = build_tool_with_llm(llm_match_id, **kwargs)
        # Persist the newly built tool in the free tier for future reuse.
        store_tool(built_tool, tier="free")
        return built_tool

    # ------------------------------------------------------------------
    # Failure
    # ------------------------------------------------------------------
    error_msg = f"Unable to resolve tool request: {request!r}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)


# ----------------------------------------------------------------------
# Convenience wrapper for external callers
# ----------------------------------------------------------------------
def get_tool(request: str, **kwargs: Any) -> Any:
    """
    Public API used by other modules to obtain a tool.

    This simply forwards to :func:`route_tool_request` but isolates the
    routing logic, making future extensions (caching layers, async support,
    etc.) straightforward.
    """
    return route_tool_request(request, **kwargs)