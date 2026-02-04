"""
Session‑level in‑memory cache with LRU eviction.

The cache stores the same shape of data as :class:`ProjectCache` but lives only
for the lifetime of the Python process.  It is useful for hot‑path look‑ups
where disk I/O would be too expensive.
"""

import collections
import time
from typing import Any, List, Tuple

from .embeddings import embed


class SessionCache:
    """
    Ephemeral cache backed by an OrderedDict (LRU).

    Each entry holds:
    - ``payload`` – the original Python object.
    - ``embedding`` – vector used for semantic similarity.
    - ``access_count`` – how many times the entry has been retrieved.
    - ``last_access`` – timestamp of the most recent access.
    """

    def __init__(self, max_size: int = 256):
        self.max_size = max_size
        self._store = collections.OrderedDict()  # key -> entry dict

    def _make_entry(self, payload: Any, embedding: List[float]) -> dict:
        return {
            "payload": payload,
            "embedding": embedding,
            "access_count": 0,
            "last_access": time.time(),
        }

    def add(self, key: str, payload: Any, embedding: List[float] = None) -> None:
        """
        Insert or update an entry.  If the cache exceeds ``max_size`` the least
        recently used item is evicted.
        """
        if embedding is None:
            embedding = embed(payload)

        if key in self._store:
            # Update existing entry and move to the end (most recent)
            entry = self._store.pop(key)
            entry.update(
                {
                    "payload": payload,
                    "embedding": embedding,
                    "last_access": time.time(),
                }
            )
        else:
            entry = self._make_entry(payload, embedding)

        self._store[key] = entry
        self._store.move_to_end(key)  # mark as most recently used

        if len(self._store) > self.max_size:
            # Evict the LRU item
            evicted_key, _ = self._store.popitem(last=False)
            # No further action needed; entry is simply dropped.

    def get(self, key: str) -> Any:
        """
        Retrieve an entry by exact key.  Access counters are updated and the
        entry is moved to the most‑recent position.
        """
        entry = self._store.get(key)
        if entry is None:
            return None
        entry["access_count"] += 1
        entry["last_access"] = time.time()
        # Move to end to reflect recent use
        self._store.move_to_end(key)
        return entry["payload"]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        import math

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Tuple[str, Any, float]]:
        """
        Semantic similarity search over the in‑memory store.

        Returns ``(key, payload, score)`` sorted by descending score.
        """
        results = []
        for key, entry in self._store.items():
            score = self._cosine_similarity(query_embedding, entry["embedding"])
            if score >= min_score:
                results.append((key, entry["payload"], score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def clear(self) -> None:
        """Empty the entire session cache."""
        self._store.clear()