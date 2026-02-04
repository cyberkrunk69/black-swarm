\"\"\"tool_router.py
Routing layer for tool lookup and assembly.

The router follows a three‑step hierarchy:

1. **Tool Store (free)** – Look for an existing, fully‑built tool in the
   persistent ``tool_store``. This operation is cheap and returns instantly
   if a match is found.

2. **Component Store (cheap)** – If no full tool exists, try to locate the
   required components in ``component_store`` and assemble a new tool from
   them. This is more expensive than step 1 but still cheap compared to a
   full LLM build.

3. **Full LLM Build (expensive)** – As a last resort, invoke the LLM builder to
   generate the tool from scratch, then store it for future reuse.

All look‑ups use a semantic search function ``semantic_search`` that returns a
list of candidate IDs ordered by relevance. The first candidate that satisfies
the request is used.

The module is deliberately self‑contained – it only imports the minimal public
interfaces that are expected to exist in the code base. If any of those
interfaces are missing, an ``ImportError`` will be raised at import time,
making the failure explicit.
\"\"\"

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Expected external interfaces (these should be provided elsewhere in the repo)
# ---------------------------------------------------------------------------
try:
    # Persistent store of fully built tools (free lookup)
    from tool_store import get_tool_by_id, semantic_search as tool_search, store_tool
except ImportError as exc:
    raise ImportError("tool_store module with required functions is missing") from exc

try:
    # Store of individual components that can be assembled into a tool
    from component_store import (
        get_component_by_id,
        semantic_search as component_search,
        assemble_tool,
    )
except ImportError as exc:
    raise ImportError("component_store module with required functions is missing") from exc

try:
    # Expensive LLM‑based builder
    from llm_builder import build_tool, semantic_search as llm_search, store_built_tool
except ImportError as exc:
    raise ImportError("llm_builder module with required functions is missing") from exc


# ---------------------------------------------------------------------------
# Core routing implementation
# ---------------------------------------------------------------------------
class ToolRouter:
    \"\"\"Route a tool request through the three‑tier hierarchy.

    Parameters
    ----------
    request : Dict[str, Any]
        A dictionary describing the desired tool. Typical keys include
        ``\"name\"``, ``\"description\"`` and optional ``\"metadata\"``.
    \"\"\"

    def __init__(self) -> None:
        # No state needed at the moment; the router is stateless.
        pass

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def route(self, request: Dict[str, Any]) -> Any:
        \"\"\"Find or build the requested tool.

        The method attempts the three strategies in order and returns the
        first successful result. If all strategies fail, a ``RuntimeError`` is
        raised.

        Returns
        -------
        Any
            The tool object (type depends on the underlying stores).

        Raises
        ------
        RuntimeError
            If the tool cannot be obtained by any strategy.
        \"\"\"
        # 1️⃣ Free lookup in the tool store
        tool = self._lookup_tool_store(request)
        if tool is not None:
            return tool

        # 2️⃣ Cheap assembly from components
        tool = self._assemble_from_components(request)
        if tool is not None:
            return tool

        # 3️⃣ Expensive full LLM build
        tool = self._build_full_tool(request)
        if tool is not None:
            return tool

        raise RuntimeError("Unable to obtain tool for the given request.")

    # -----------------------------------------------------------------------
    # Strategy 1 – Tool Store (free)
    # -----------------------------------------------------------------------
    def _lookup_tool_store(self, request: Dict[str, Any]) -> Optional[Any]:
        \"\"\"Search the tool store using semantic similarity.

        Parameters
        ----------
        request : Dict[str, Any]

        Returns
        -------
        Optional[Any]
            The matched tool or ``None`` if no suitable tool is found.
        \"\"\"
        # Perform a semantic search; the underlying implementation decides the
        # embedding model and similarity metric.
        candidate_ids: List[str] = tool_search(request)

        for tool_id in candidate_ids:
            tool = get_tool_by_id(tool_id)
            if self._tool_matches(tool, request):
                return tool
        return None

    # -----------------------------------------------------------------------
    # Strategy 2 – Component Assembly (cheap)
    # -----------------------------------------------------------------------
    def _assemble_from_components(self, request: Dict[str, Any]) -> Optional[Any]:
        \"\"\"Try to build the tool from existing components.

        The function first finds candidate component IDs via semantic search,
        fetches them, and then calls ``assemble_tool``. If assembly succeeds,
        the new tool is stored back into the tool store for future fast look‑up.
        \"\"\"
        candidate_ids: List[str] = component_search(request)

        # Gather components; abort if any component cannot be retrieved.
        components = []
        for comp_id in candidate_ids:
            comp = get_component_by_id(comp_id)
            if comp is None:
                continue
            components.append(comp)

        if not components:
            return None

        try:
            tool = assemble_tool(components, request)
        except Exception:  # pragma: no cover – defensive; concrete lib may raise
            return None

        # Store the newly assembled tool for future free look‑ups.
        try:
            store_tool(tool)
        except Exception:
            # Storing failure shouldn't block the return of a usable tool.
            pass

        return tool

    # -----------------------------------------------------------------------
    # Strategy 3 – Full LLM Build (expensive)
    # -----------------------------------------------------------------------
    def _build_full_tool(self, request: Dict[str, Any]) -> Optional[Any]:
        \"\"\"Generate the tool from scratch using the LLM builder.

        This is the most resource‑intensive path, so it is only used when the
        previous strategies fail. The built tool is persisted via
        ``store_built_tool``.
        \"\"\"
        # Optionally perform a semantic search within the LLM space to guide
        # generation (e.g., retrieve similar prompts). The LLM builder itself
        # decides how to use the search results.
        similar_prompts: List[str] = llm_search(request)

        try:
            tool = build_tool(request, similar_prompts)
        except Exception:
            return None

        # Persist the freshly built tool.
        try:
            store_built_tool(tool)
        except Exception:
            pass

        return tool

    # -----------------------------------------------------------------------
    # Helper – simple matching heuristic
    # -----------------------------------------------------------------------
    @staticmethod
    def _tool_matches(tool: Any, request: Dict[str, Any]) -> bool:
        \"\"\"Very lightweight check that a tool satisfies the request.

        The default implementation checks that the tool's ``name`` or
        ``description`` contains the request ``name`` (case‑insensitive). This
        can be overridden with a more sophisticated predicate if needed.
        \"\"\"
        req_name = request.get(\"name\", \"\").lower()
        if not req_name:
            return True  # If no name is specified, accept any candidate.

        tool_name = getattr(tool, \"name\", \"\").lower()
        tool_desc = getattr(tool, \"description\", \"\").lower()

        return req_name in tool_name or req_name in tool_desc


# ---------------------------------------------------------------------------
# Convenience function for external callers
# ---------------------------------------------------------------------------
def route_tool(request: Dict[str, Any]) -> Any:
    \"\"\"Utility wrapper around :class:`ToolRouter`.

    Example
    -------
    >>> from tool_router import route_tool
    >>> my_tool = route_tool({\"name\": \"image‑classifier\"})
    \"\"\"
    router = ToolRouter()
    return router.route(request)