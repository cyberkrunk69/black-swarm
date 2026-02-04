"""Expert Knowledge Cache package.

Provides:
- ProjectCache: persistent, disk‑backed cache shared across sessions.
- SessionCache: transient, in‑memory cache scoped to a single execution.
- Semantic lookup using vector embeddings.
- LRU pruning with access‑frequency weighting.
"""
from .cache import ProjectCache, SessionCache, embed_text

__all__ = ["ProjectCache", "SessionCache", "embed_text"]