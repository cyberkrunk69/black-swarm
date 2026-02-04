"""
In‑memory, session‑level cache.

Features:
- Stores payload + embedding for rapid lookup.
- LRU eviction with frequency weighting (same heuristic as the persistent cache).
- Ephemeral: lives only for the duration of the Python process / session.
"""

import time
from collections import OrderedDict
from typing import Any, Optional, Tuple

import numpy as np

from .embedding_utils import embed_text


class SessionCacheEntry:
    __slots__ = ("payload", "embedding", "last_access", "access_count")

    def __init__(self, payload: Any, embedding: np.ndarray):
        self.payload = payload
        self.embedding = embedding
        now = time.time()
        self.last_access = now
        self.access_count = 1


class SessionCache:
    """
    Simple LRU cache with frequency weighting.
    """

    def __init__(self, max_entries: int = 1_000, embedding_dim: int = 384):
        self.max_entries = max_entries
        self.embedding_dim = embedding_dim
        # OrderedDict preserves insertion order; we will move accessed items to the end.
        self._store: OrderedDict[str, SessionCacheEntry] = OrderedDict()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def set(self, key: str, payload: Any, text_for_embedding: str) -> None:
        """
        Insert or replace an entry.
        """
        embedding = embed_text(text_for_embedding, dim=self.embedding_dim)
        entry = SessionCacheEntry(payload, embedding)

        if key in self._store:
            # Replace existing entry
            del self._store[key]
        self._store[key] = entry
        self._store.move_to_end(key)  # mark as most-recently used

        self._prune_if_necessary()

    def get(
        self,
        query_text: str,
        top_k: int = 1,
        min_score: float = 0.7,
    ) -> Optional[Tuple[str, Any, float]]:
        """
        Semantic lookup inside the session cache.

        Returns the best matching (key, payload, similarity) or ``None``.
        """
        if not self._store:
            return None

        query_vec = embed_text(query_text, dim=self.embedding_dim)

        best_match: Optional[Tuple[float, str, Any]] = None
        for key, entry in self._store.items():
            score = float(np.dot(query_vec, entry.embedding))  # vectors are normalised
            if score >= min_score and (best_match is None or score > best_match[0]):
                best_match = (score, key, entry)

        if best_match is None:
            return None

        score, key, entry = best_match
        # Update metadata
        entry.last_access = time.time()
        entry.access_count += 1
        # Move to end to reflect recent use
        self._store.move_to_end(key)

        return key, entry.payload, score

    # --------------------------------------------------------------------- #
    # Pruning
    # --------------------------------------------------------------------- #
    def _prune_if_necessary(self) -> None:
        """
        Evict items when the cache exceeds ``max_entries``.
        Uses the same heuristic as the persistent cache:
            eviction_score = (now - last_access) / access_count
        """
        while len(self._store) > self.max_entries:
            now = time.time()
            # Find key with highest eviction score
            evict_key, _ = max(
                self._store.items(),
                key=lambda kv: (now - kv[1].last_access) / kv[1].access_count,
            )
            del self._store[evict_key]