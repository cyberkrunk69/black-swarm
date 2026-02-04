"""
CacheManager – unified interface for:

* Project‑level persistent cache (stored on disk via ``shelve``)
* Session‑level in‑memory cache (ephemeral, LRU‑pruned)

Semantic lookup is performed by comparing the query embedding against stored
embeddings and returning the most similar entry if its similarity exceeds a
configurable threshold (default 0.75).

Typical usage:

    from expert_cache import CacheManager

    cm = CacheManager()
    result = cm.get("some query")
    if result is None:
        # compute answer, then store it
        cm.set("some query", answer)
"""
import os
import shelve
import time
from typing import Any, Optional, Tuple, List

import numpy as np

from .config import PROJECT_CACHE_PATH, SESSION_CACHE_MAX_ITEMS
from .embedding_search import embed_texts, top_k_similar
from .lru_pruner import prune_cache

CacheEntry = Tuple[Any, np.ndarray, int, float]  # (value, embedding, freq, last_ts)


class CacheManager:
    """
    Unified cache handling class.

    Attributes
    ----------
    _session_cache : dict
        In‑memory dict keyed by a string identifier. Values are ``CacheEntry``.
    _project_shelf : shelve.DbfilenameShelf
        Persistent on‑disk cache. Stored values are also ``CacheEntry``.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self._session_cache: dict[str, CacheEntry] = {}
        self._similarity_threshold = similarity_threshold

        # Ensure the directory for the persistent cache exists
        os.makedirs(os.path.dirname(PROJECT_CACHE_PATH), exist_ok=True)
        # Use writeback=False for speed; we manually rewrite entries on updates.
        self._project_shelf = shelve.open(PROJECT_CACHE_PATH, flag="c", writeback=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, query: str) -> Optional[Any]:
        """
        Retrieve a cached value semantically similar to ``query``.

        The method first checks the session cache, then the persistent cache.
        If a match is found with similarity >= threshold, the entry's
        frequency counters are updated and the stored value is returned.

        Parameters
        ----------
        query : str
            The textual query for which a cached answer is desired.

        Returns
        -------
        Any or None
            Cached value if a sufficiently similar entry exists, otherwise None.
        """
        query_emb = embed_texts([query])[0]  # shape (D,)

        # 1️⃣ Session cache lookup
        result = self._semantic_lookup(query_emb, self._session_cache)
        if result is not None:
            return result

        # 2️⃣ Persistent cache lookup
        result = self._semantic_lookup(query_emb, self._project_shelf)
        if result is not None:
            # Promote to session cache for faster subsequent access
            self._add_to_session_cache(result[0], result[1])
            return result[0]

        return None

    def set(self, key: str, value: Any) -> None:
        """
        Store ``value`` under ``key`` in both caches.

        The key is stored verbatim; embeddings are derived from ``key``.
        Frequency counters start at 1 and timestamps are set to ``time.time()``.

        Parameters
        ----------
        key : str
            Identifier (typically the original user query).
        value : Any
            Arbitrary Python object that can be pickled (shelve requirement).
        """
        embedding = embed_texts([key])[0]  # (D,)

        entry: CacheEntry = (value, embedding, 1, time.time())

        # Session cache (ephemeral)
        self._session_cache[key] = entry
        prune_cache(self._session_cache)

        # Persistent cache (project level)
        self._project_shelf[key] = entry
        self._project_shelf.sync()

    def close(self) -> None:
        """Close the persistent shelf – should be called on shutdown."""
        self._project_shelf.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _semantic_lookup(
        self, query_emb: np.ndarray, store: dict
    ) -> Optional[Tuple[Any, np.ndarray]]:
        """
        Perform a semantic similarity search within ``store``.

        Returns a tuple (value, embedding) of the best match if its similarity
        exceeds the configured threshold; otherwise ``None``.
        """
        if not store:
            return None

        # Gather embeddings
        keys = list(store.keys())
        embeddings = np.stack([store[k][1] for k in keys])  # shape (N, D)

        idxs, sims = top_k_similar(query_emb, embeddings, k=1)
        if len(idxs) == 0:
            return None

        best_idx = idxs[0]
        best_sim = sims[0]

        if best_sim >= self._similarity_threshold:
            best_key = keys[best_idx]
            value, emb, freq, _ = store[best_key]
            # Update frequency & timestamp
            store[best_key] = (value, emb, freq + 1, time.time())
            return value, emb

        return None

    def _add_to_session_cache(self, value: Any, embedding: np.ndarray) -> None:
        """
        Helper to insert a value into the session cache without recomputing the embedding.
        """
        # Use a synthetic key based on embedding hash to avoid collisions.
        synthetic_key = f"_auto_{hash(embedding.tobytes())}"
        entry: CacheEntry = (value, embedding, 1, time.time())
        self._session_cache[synthetic_key] = entry
        prune_cache(self._session_cache)