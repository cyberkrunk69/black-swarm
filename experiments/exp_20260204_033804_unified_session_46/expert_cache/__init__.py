"""
Expert Knowledge Cache package.

Provides:
- ProjectCache: persistent, disk‑backed cache shared across sessions.
- SessionCache: in‑memory, ephemeral cache for a single execution.
- Embedding utilities for semantic lookup.
- LRU pruning with frequency‑weighted eviction.
"""
from .cache import ProjectCache, SessionCache, embed_text, semantic_search