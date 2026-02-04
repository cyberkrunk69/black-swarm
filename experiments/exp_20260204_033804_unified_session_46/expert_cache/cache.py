"""
expert_cache/cache.py

Implements a two‑tier caching system:

1. ProjectCache
   • Persistent on‑disk storage (uses `shelve`).
   • Stores: key → {"value": ..., "embedding": ..., "access_cnt": int, "last_access": float}
   • Provides semantic lookup via cosine similarity of stored embeddings.
   • LRU‑style pruning that respects access frequency (items with low `access_cnt`
     and older `last_access` are evicted first).

2. SessionCache
   • Pure in‑memory cache for the current session.
   • Same data schema as ProjectCache but lives only for the life of the process.

Both caches share the same embedding utilities so that look‑ups are consistent
across tiers.

The implementation purposefully avoids heavy external dependencies; a
light‑weight placeholder embedding function is provided.  In a production
environment you would replace `embed_text` with a real model (e.g. Sentence‑
Transformers).
"""

import os
import time
import json
import math
import shelve
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Optional

# --------------------------------------------------------------------------- #
# Embedding utilities (placeholder – replace with real model in production)   #
# --------------------------------------------------------------------------- #

def embed_text(text: str) -> List[float]:
    """
    Convert a string into a fixed‑size vector.

    The placeholder implementation creates a deterministic pseudo‑embedding
    based on character codes.  Replace this with a call to a real embedding
    model (e.g., `SentenceTransformer('all-MiniLM-L6-v2')`).

    Returns
    -------
    List[float]
        Normalised embedding vector.
    """
    # Simple deterministic hash‑based embedding (size = 64)
    size = 64
    vec = [0.0] * size
    for i, ch in enumerate(text.encode("utf-8")):
        idx = i % size
        vec[idx] += (ch % 255) / 255.0
    # L2‑normalise
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Return cosine similarity between two equal‑length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    # vectors are already normalised, but guard against zero‑norm
    return dot

def semantic_search(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Tuple[Dict[str, Any], float]]:
    """
    Perform a semantic similarity search over a list of cached entries.

    Parameters
    ----------
    query : str
        The query string.
    candidates : List[Dict]
        Each dict must contain an ``embedding`` key with a List[float].
    top_k : int, optional
        Number of results to return.

    Returns
    -------
    List[Tuple[Dict, float]]
        Sorted list (best first) of (entry, similarity) tuples.
    """
    q_emb = embed_text(query)
    scored = []
    for entry in candidates:
        emb = entry.get("embedding")
        if emb is None:
            continue
        sim = _cosine_similarity(q_emb, emb)
        scored.append((entry, sim))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]

# --------------------------------------------------------------------------- #
# Core cache classes                                                          #
# --------------------------------------------------------------------------- #

class _BaseCache:
    """
    Shared logic for both ProjectCache and SessionCache.
    """

    def __init__(self):
        self._lock = threading.RLock()

    def _make_record(self, value: Any, embedding: Optional[List[float]]) -> Dict[str, Any]:
        return {
            "value": value,
            "embedding": embedding,
            "access_cnt": 0,
            "last_access": time.time(),
        }

    def _touch(self, record: Dict[str, Any]) -> None:
        record["access_cnt"] += 1
        record["last_access"] = time.time()

    @staticmethod
    def _score_for_prune(record: Dict[str, Any]) -> float:
        """
        Lower score → more likely to be evicted.

        Combines inverse access count and recency.
        """
        age = time.time() - record["last_access"]
        # Add 1 to avoid division by zero.
        return age / (record["access_cnt"] + 1)

    @staticmethod
    def _sort_by_prune_score(cache_dict: Dict[str, Dict[str, Any]]) -> List[Tuple[str, float]]:
        return sorted(
            ((k, _BaseCache._score_for_prune(v)) for k, v in cache_dict.items()),
            key=lambda kv: kv[1],
            reverse=False,
        )

# --------------------------------------------------------------------------- #
# Persistent project‑level cache                                               #
# --------------------------------------------------------------------------- #

class ProjectCache(_BaseCache):
    """
    Disk‑backed cache shared across all sessions of the project.

    Data is stored in a `shelve` database under the experiment’s root directory.
    """

    def __init__(self, cache_dir: str = "expert_cache_data", max_items: int = 10_000):
        super().__init__()
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)
        self.db_path = os.path.join(self.cache_dir, "project_cache.db")
        self.max_items = max_items

        # `writeback=True` enables mutable entries to be updated in‑place.
        self._db = shelve.open(self.db_path, writeback=True)

    def __del__(self):
        try:
            self._db.close()
        except Exception:
            pass

    # ------------------------------------------------------------------- #
    # CRUD operations                                                    #
    # ------------------------------------------------------------------- #

    def set(self, key: str, value: Any, embed: bool = True) -> None:
        """
        Store ``value`` under ``key``.  If ``embed`` is True, an embedding for the
        string representation of ``value`` is also stored for semantic lookup.
        """
        with self._lock:
            embedding = embed_text(str(value)) if embed else None
            self._db[key] = self._make_record(value, embedding)
            self._db.sync()
            self._maybe_prune()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve the cached value for ``key``.  Returns ``default`` if the key
        does not exist.
        """
        with self._lock:
            rec = self._db.get(key)
            if rec is None:
                return default
            self._touch(rec)
            self._db[key] = rec  # writeback update
            self._db.sync()
            return rec["value"]

    def delete(self, key: str) -> None:
        """Remove ``key`` from the cache if present."""
        with self._lock:
            if key in self._db:
                del self._db[key]
                self._db.sync()

    def exists(self, key: str) -> bool:
        """Return True if ``key`` is cached."""
        with self._lock:
            return key in self._db

    # ------------------------------------------------------------------- #
    # Semantic lookup                                                    #
    # ------------------------------------------------------------------- #

    def semantic_lookup(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[Any, float]]:
        """
        Perform a semantic search over all cached entries.

        Returns a list of (value, similarity) tuples.
        """
        with self._lock:
            candidates = [
                {"key": k, "value": rec["value"], "embedding": rec["embedding"]}
                for k, rec in self._db.items()
                if rec.get("embedding") is not None
            ]
        results = semantic_search(query, candidates, top_k=top_k)
        return [(r["value"], score) for r, score in results]

    # ------------------------------------------------------------------- #
    # Pruning                                                            #
    # ------------------------------------------------------------------- #

    def _maybe_prune(self) -> None:
        """
        Prune the cache if it exceeds ``max_items``.  Eviction respects both
        recency and access frequency.
        """
        with self._lock:
            if len(self._db) <= self.max_items:
                return

            # Determine how many items to drop (e.g., 10% of max size)
            target_size = int(self.max_items * 0.9)
            to_evict = len(self._db) - target_size

            # Build a list of (key, score) where lower scores are evicted first
            scores = self._sort_by_prune_score(dict(self._db))
            for key, _score in scores[:to_evict]:
                del self._db[key]

            self._db.sync()

    # ------------------------------------------------------------------- #
    # Utility                                                            #
    # ------------------------------------------------------------------- #

    def dump_metadata(self, path: Optional[str] = None) -> str:
        """
        Export a JSON snapshot of the cache metadata (keys, access counts,
        timestamps).  Useful for debugging or external inspection.
        """
        meta = {
            k: {
                "access_cnt": v["access_cnt"],
                "last_access": v["last_access"],
                "has_embedding": v["embedding"] is not None,
            }
            for k, v in self._db.items()
        }
        json_str = json.dumps(meta, indent=2, sort_keys=True)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(json_str)
        return json_str

# --------------------------------------------------------------------------- #
# Session‑level in‑memory cache                                                #
# --------------------------------------------------------------------------- #

class SessionCache(_BaseCache):
    """
    Ephemeral, in‑memory cache for a single runtime session.

    Internally uses an ``OrderedDict`` to preserve insertion order, which aids
    LRU eviction.  The public API mirrors ``ProjectCache`` where appropriate.
    """

    def __init__(self, max_items: int = 1_000):
        super().__init__()
        self.max_items = max_items
        self._store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    # ------------------------------------------------------------------- #
    # CRUD operations                                                    #
    # ------------------------------------------------------------------- #

    def set(self, key: str, value: Any, embed: bool = True) -> None:
        with self._lock:
            embedding = embed_text(str(value)) if embed else None
            self._store[key] = self._make_record(value, embedding)
            self._store.move_to_end(key)  # mark as most‑recently used
            self._maybe_prune()

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            rec = self._store.get(key)
            if rec is None:
                return default
            self._touch(rec)
            self._store.move_to_end(key)
            return rec["value"]

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    # ------------------------------------------------------------------- #
    # Semantic lookup                                                    #
    # ------------------------------------------------------------------- #

    def semantic_lookup(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Tuple[Any, float]]:
        with self._lock:
            candidates = [
                {"key": k, "value": rec["value"], "embedding": rec["embedding"]}
                for k, rec in self._store.items()
                if rec.get("embedding") is not None
            ]
        results = semantic_search(query, candidates, top_k=top_k)
        return [(r["value"], score) for r, score in results]

    # ------------------------------------------------------------------- #
    # Pruning                                                            #
    # ------------------------------------------------------------------- #

    def _maybe_prune(self) -> None:
        """
        Evict least‑used items until the cache size is below ``max_items``.
        The eviction order respects the weighted LRU score.
        """
        with self._lock:
            if len(self._store) <= self.max_items:
                return

            # Compute scores for all items
            scores = self._sort_by_prune_score(dict(self._store))
            # Determine number to drop (reduce to 90% of max_items)
            target = int(self.max_items * 0.9)
            to_remove = len(self._store) - target
            for key, _score in scores[:to_remove]:
                self._store.pop(key, None)

    # ------------------------------------------------------------------- #
    # Utility                                                            #
    # ------------------------------------------------------------------- #

    def dump_metadata(self) -> str:
        """Return JSON representation of in‑memory cache metadata."""
        meta = {
            k: {
                "access_cnt": v["access_cnt"],
                "last_access": v["last_access"],
                "has_embedding": v["embedding"] is not None,
            }
            for k, v in self._store.items()
        }
        return json.dumps(meta, indent=2, sort_keys=True)

# --------------------------------------------------------------------------- #
# Convenience singleton instances (optional)                                  #
# --------------------------------------------------------------------------- #

# By default, expose a project‑wide cache rooted at the experiment directory.
_default_project_cache = ProjectCache(
    cache_dir=os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "..",
        "expert_cache_data"
    ),
    max_items=20_000,
)

def get_project_cache() -> ProjectCache:
    """Return a shared ProjectCache instance."""
    return _default_project_cache

def new_session_cache(max_items: int = 1_000) -> SessionCache:
    """Factory for a fresh SessionCache."""
    return SessionCache(max_items=max_items)