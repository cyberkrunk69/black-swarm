"""Expert Knowledge Cache package.

Provides:
- PersistentCache: project‑level, disk‑backed cache with semantic lookup.
- SessionCache: in‑memory, session‑level cache with LRU + frequency weighting.
- CacheManager: façade that routes requests to the appropriate cache.
"""