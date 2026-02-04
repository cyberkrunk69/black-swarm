"""
Cache implementation for the unified session experiment.

Two layers:
- ProjectCache: persisted on disk (pickle file) – shared across all sessions.
- SessionCache: in‑memory only – lives for the duration of a session.

Both expose `add`, `lookup`, and `prune` methods.
Semantic lookup is performed by comparing the embedding of the query
against stored embeddings using cosine similarity.
"""

import os
import pickle
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .embeddings import embed_text
from .lru import WeightedLRU

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache_storage"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PROJECT_CACHE_PATH = CACHE_DIR / "project_cache.pkl"


class CacheEntry:
    """
    Represents a single cached item.

    Attributes
    ----------
    key: str
        Human readable identifier (e.g., a prompt or a short description).
    value: Any
        The artefact to be cached (could be a string, dict, model output, etc.).
    embedding: np.ndarray
        Vector representation used for semantic similarity search.
    metadata: dict
        Optional auxiliary information.
    """

    __slots__ = ("key", "value", "embedding", "metadata")

    def __init__(self, key: str, value: Any, embedding: np.ndarray, metadata: Optional[Dict] = None):
        self.key = key
        self.value = value
        self.embedding = embedding.astype(np.float32)
        self.metadata = metadata or {}

    def to_tuple(self) -> Tuple[str, Any, List[float], Dict]:
        return (self.key, self.value, self.embedding.tolist(), self.metadata)

    @staticmethod
    def from_tuple(tpl: Tuple[str, Any, List[float], Dict]) -> "CacheEntry":
        key, value, emb_list, meta = tpl
        return CacheEntry(key, value, np.array(emb_list, dtype=np.float32), meta)


class BaseCache:
    """Common functionality for both ProjectCache and SessionCache."""

    def __init__(self, max_items: int = 5_000, embed_dim: int = 128):
        self.max_items = max_items
        self.embed_dim = embed_dim
        self._lru = WeightedLRU(max_items=self.max_items)
        self._lock = threading.RLock()

    def _embed(self, text: str) -> np.ndarray:
        return embed_text([text], dim=self.embed_dim)[0]

    def add(self, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        """Add a new entry to the cache (or replace existing)."""
        with self._lock:
            emb = self._embed(key)
            entry = CacheEntry(key, value, emb, metadata)
            self._lru.set(key, entry)

    def _all_entries(self) -> List[CacheEntry]:
        return [entry for _, entry in self._lru.items()]

    def lookup(self, query: str, top_k: int = 3, similarity_threshold: float = 0.6) -> List[CacheEntry]:
        """
        Perform a semantic search over cached keys.

        Returns up to `top_k` entries whose cosine similarity with the
        query embedding exceeds `similarity_threshold`. Results are sorted
        by descending similarity.
        """
        with self._lock:
            if not self._lru.store:
                return []

            query_emb = self._embed(query).astype(np.float32)

            # Stack embeddings for vectorised similarity
            entries = self._all_entries()
            emb_matrix = np.stack([e.embedding for e in entries])

            # Cosine similarity (vectors are already normalised)
            sims = np.dot(emb_matrix, query_emb)

            # Filter & sort
            idxs = np.where(sims >= similarity_threshold)[0]
            if idxs.size == 0:
                return []

            sorted_idx = idxs[np.argsort(-sims[idxs])]
            top_idx = sorted_idx[:top_k]

            return [entries[i] for i in top_idx]

    def prune(self) -> None:
        """Trigger LRU pruning explicitly."""
        with self._lock:
            self._lru.prune()

    def clear(self) -> None:
        with self._lock:
            self._lru.clear()


class ProjectCache(BaseCache):
    """
    Persistent, project‑level cache stored on disk.
    Thread‑safe singleton per process.
    """

    _instance: Optional["ProjectCache"] = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super(ProjectCache, cls).__new__(cls)
        return cls._instance

    def __init__(self, max_items: int = 10_000, embed_dim: int = 128):
        # Ensure __init__ runs only once
        if getattr(self, "_initialized", False):
            return
        super().__init__(max_items=max_items, embed_dim=embed_dim)
        self._load_from_disk()
        self._initialized = True

    def _load_from_disk(self) -> None:
        if PROJECT_CACHE_PATH.is_file():
            try:
                with PROJECT_CACHE_PATH.open("rb") as f:
                    raw = pickle.load(f)
                for key, entry_tpl in raw.items():
                    entry = CacheEntry.from_tuple(entry_tpl)
                    self._lru.set(key, entry)
            except Exception as e:
                # Corrupted cache – start fresh
                print(f"[ProjectCache] Failed to load cache ({e}); starting empty.")
        else:
            # No existing cache
            pass

    def _persist_to_disk(self) -> None:
        data = {k: v.to_tuple() for k, v in self._lru.items()}
        with PROJECT_CACHE_PATH.open("wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def add(self, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        super().add(key, value, metadata)
        self._persist_to_disk()

    def prune(self) -> None:
        super().prune()
        self._persist_to_disk()

    def clear(self) -> None:
        super().clear()
        self._persist_to_disk()


class SessionCache(BaseCache):
    """
    Ephemeral, per‑session cache. Lives only in memory.
    """

    def __init__(self, session_id: str, max_items: int = 2_000, embed_dim: int = 128):
        super().__init__(max_items=max_items, embed_dim=embed_dim)
        self.session_id = session_id

    # Inherits all behaviour from BaseCache; no persistence needed.