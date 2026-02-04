"""
expert_cache package

Provides:
- ProjectCache: persistent, disk‑backed cache shared across all sessions.
- SessionCache: ephemeral, in‑memory cache scoped to a single session.
- Semantic lookup using simple embedding + cosine similarity.
- LRU pruning with frequency weighting.
"""

from .cache import ProjectCache, SessionCache, CacheEntry
from .embeddings import embed_text