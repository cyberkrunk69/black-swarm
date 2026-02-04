"""
Expert Knowledge Cache package.

Provides:
- ProjectLevelCache: persistent, disk‑backed cache (SQLite) that survives across sessions.
- SessionLevelCache: in‑memory, ephemeral cache scoped to a single execution.
- ExpertCache: façade that combines both, offering semantic lookup via embeddings,
  LRU pruning weighted by access frequency, and a simple API: `get`, `set`, `search`.

The implementation is deliberately lightweight and has no external heavy dependencies.
If a real embedding model is available, replace `embed_text` with the appropriate call.
"""
from .cache import ExpertCache, ProjectLevelCache, SessionLevelCache

__all__ = ["ExpertCache", "ProjectLevelCache", "SessionLevelCache"]