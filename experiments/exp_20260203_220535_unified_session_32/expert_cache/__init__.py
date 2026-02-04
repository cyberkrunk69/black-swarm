"""
expert_cache package – provides a two‑tier caching system:

* **ProjectCache** – persistent, file‑based storage that survives across
  sessions.  It stores vectors (embeddings) together with the original
  payload and is backed by a SQLite database for durability and fast
  nearest‑neighbor lookup.

* **SessionCache** – in‑memory, short‑lived cache for the current
  execution session.  It uses an LRU policy that also accounts for
  access frequency (LFU‑weighted LRU) to keep the most useful items.

* **CacheManager** – façade that coordinates look‑ups across the two
  tiers, performs semantic similarity search using stored embeddings,
  and handles automatic pruning.

Only the public classes are exported; internal helpers live in
`cache_manager.py`.
"""

from .cache_manager import CacheManager, ProjectCache, SessionCache

__all__ = ["CacheManager", "ProjectCache", "SessionCache"]