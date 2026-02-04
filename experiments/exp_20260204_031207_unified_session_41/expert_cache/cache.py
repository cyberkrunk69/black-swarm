"""
expert_cache/cache.py
---------------------

Core implementation of the unified expert knowledge cache.

Features
~~~~~~~~
* **Project‑level persistent cache** – stored in a SQLite database (`project_cache.db`).
  Entries survive across process restarts and are shared by all sessions.
* **Session‑level ephemeral cache** – pure‑Python in‑memory store that is cleared when the
  Python interpreter exits.
* **Semantic search** – each entry stores an embedding vector.  Look‑ups can be performed
  via cosine similarity against a query embedding.
* **LRU pruning with frequency weighting** – the cache tracks `last_access` timestamps
  and an `access_count`.  When the size limit is exceeded, the least‑valuable entries
  (old *and* rarely accessed) are evicted.

The design purposefully avoids heavyweight ML libraries; a placeholder `embed_text`
function using NumPy random vectors is provided.  Replace it with a real model
(e.g., SentenceTransformer) when available.
"""

import os
import json
import time
import sqlite3
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Tuple, Optional

import numpy as np

# --------------------------------------------------------------------------- #
# Helper: simple deterministic embedding stub
# --------------------------------------------------------------------------- #
def embed_text(text: str, dim: int = 128) -> np.ndarray:
    """
    Produce a deterministic pseudo‑embedding for a given text.
    In production replace this with a real model (e.g., sentence‑transformers).

    Parameters
    ----------
    text: str
        Input text.
    dim: int, default 128
        Dimensionality of the embedding.

    Returns
    -------
    np.ndarray
        Normalised embedding vector.
    """
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.normal(size=dim)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two 1‑D arrays."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


# --------------------------------------------------------------------------- #
# Session‑level cache (ephemeral)
# --------------------------------------------------------------------------- #
class SessionLevelCache:
    """
    Simple in‑memory LRU cache with frequency weighting.

    The internal store is an ``OrderedDict`` where the order reflects recency.
    Each entry holds:
        - ``value``: the cached payload
        - ``embedding``: pre‑computed embedding vector (np.ndarray)
        - ``access_count``: how many times the entry has been accessed
        - ``last_access``: timestamp of the most recent access
    """

    def __init__(self, max_items: int = 256):
        self.max_items = max_items
        self.store: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self.lock = threading.RLock()

    def _prune_if_necessary(self):
        """Evict items while respecting LRU + frequency weighting."""
        with self.lock:
            while len(self.store) > self.max_items:
                # Choose candidate with lowest (access_count, last_access)
                key, _ = min(
                    self.store.items(),
                    key=lambda kv: (kv[1]["access_count"], kv[1]["last_access"]),
                )
                self.store.pop(key)

    def set(self, key: str, value: Any, embedding: Optional[np.ndarray] = None):
        """Insert or update a cache entry."""
        with self.lock:
            now = time.time()
            if embedding is None:
                embedding = embed_text(key)

            entry = {
                "value": value,
                "embedding": embedding,
                "access_count": 1,
                "last_access": now,
            }
            self.store[key] = entry
            self.store.move_to_end(key)  # mark as most‑recent
            self._prune_if_necessary()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value, updating LRU metadata."""
        with self.lock:
            entry = self.store.get(key)
            if entry is None:
                return None
            entry["access_count"] += 1
            entry["last_access"] = time.time()
            self.store.move_to_end(key)
            return entry["value"]

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, Any, float]]:
        """
        Semantic search over stored embeddings.

        Returns a list of ``(key, value, similarity)`` tuples sorted by descending similarity.
        """
        with self.lock:
            if not self.store:
                return []

            q_emb = embed_text(query)
            results = []
            for key, entry in self.store.items():
                sim = cosine_similarity(q_emb, entry["embedding"])
                results.append((key, entry["value"], sim))

            results.sort(key=lambda x: x[2], reverse=True)
            return results[:top_k]


# --------------------------------------------------------------------------- #
# Project‑level cache (persistent)
# --------------------------------------------------------------------------- #
class ProjectLevelCache:
    """
    SQLite‑backed persistent cache.

    Table schema:
        key TEXT PRIMARY KEY,
        value BLOB (JSON‑serialized),
        embedding BLOB (numpy float32 array, stored via ``np.save`` to a bytes buffer),
        access_count INTEGER,
        last_access REAL
    """

    def __init__(self, db_path: Optional[str] = None, max_items: int = 4096):
        self.db_path = db_path or os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "project_cache.db"
        )
        self.max_items = max_items
        self.lock = threading.RLock()
        self._ensure_db()

    def _ensure_db(self):
        with self.lock, sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    embedding BLOB,
                    access_count INTEGER,
                    last_access REAL
                )
                """
            )
            conn.commit()

    def _serialize_embedding(self, emb: np.ndarray) -> bytes:
        """Store embedding as raw float32 bytes."""
        return emb.astype(np.float32).tobytes()

    def _deserialize_embedding(self, blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32)

    def set(self, key: str, value: Any, embedding: Optional[np.ndarray] = None):
        """Insert or update a cache entry."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            now = time.time()
            if embedding is None:
                embedding = embed_text(key)

            payload = json.dumps(value, ensure_ascii=False)
            emb_blob = self._serialize_embedding(embedding)

            conn.execute(
                """
                INSERT INTO cache (key, value, embedding, access_count, last_access)
                VALUES (?, ?, ?, 1, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value=excluded.value,
                    embedding=excluded.embedding,
                    access_count=cache.access_count + 1,
                    last_access=excluded.last_access
                """,
                (key, payload, emb_blob, now),
            )
            conn.commit()
            self._prune_if_necessary(conn)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value, updating usage statistics."""
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT value, access_count FROM cache WHERE key = ?", (key,)
            )
            row = cur.fetchone()
            if row is None:
                return None

            value_json, access_count = row
            # Update metadata
            conn.execute(
                """
                UPDATE cache
                SET access_count = ?, last_access = ?
                WHERE key = ?
                """,
                (access_count + 1, time.time(), key),
            )
            conn.commit()
            return json.loads(value_json)

    def _prune_if_necessary(self, conn: sqlite3.Connection):
        """Evict least‑valuable rows when size limit is exceeded."""
        cur = conn.execute("SELECT COUNT(*) FROM cache")
        (count,) = cur.fetchone()
        if count <= self.max_items:
            return

        # Compute a simple score: access_count / (now - last_access + 1)
        now = time.time()
        cur = conn.execute(
            """
            SELECT key, access_count, last_access
            FROM cache
            ORDER BY (access_count / ( ? - last_access + 1 )) ASC
            LIMIT ?
            """,
            (now, count - self.max_items),
        )
        keys_to_evict = [row[0] for row in cur.fetchall()]
        if keys_to_evict:
            conn.executemany(
                "DELETE FROM cache WHERE key = ?", [(k,) for k in keys_to_evict]
            )
            conn.commit()

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, Any, float]]:
        """
        Perform a semantic similarity search across all persisted entries.

        Returns a list of ``(key, value, similarity)`` sorted by similarity descending.
        """
        with self.lock, sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT key, value, embedding FROM cache"
            )
            rows = cur.fetchall()
            if not rows:
                return []

            q_emb = embed_text(query)
            results = []
            for key, value_json, emb_blob in rows:
                emb = self._deserialize_embedding(emb_blob)
                sim = cosine_similarity(q_emb, emb)
                results.append((key, json.loads(value_json), sim))

            results.sort(key=lambda x: x[2], reverse=True)
            return results[:top_k]


# --------------------------------------------------------------------------- #
# Unified façade
# --------------------------------------------------------------------------- #
class ExpertCache:
    """
    High‑level cache that first checks the session cache, then falls back to the
    persistent project cache.  Writes are mirrored to both layers.

    Typical usage::

        cache = ExpertCache()
        cache.set("my_key", {"answer": 42})
        payload = cache.get("my_key")
        similar = cache.search("find similar knowledge")
    """

    def __init__(
        self,
        session_max_items: int = 256,
        project_max_items: int = 4096,
        db_path: Optional[str] = None,
    ):
        self.session = SessionLevelCache(max_items=session_max_items)
        self.project = ProjectLevelCache(db_path=db_path, max_items=project_max_items)

    # ------------------------------------------------------------------- #
    # Mutations
    # ------------------------------------------------------------------- #
    def set(self, key: str, value: Any, embedding: Optional[np.ndarray] = None):
        """
        Store ``value`` under ``key`` in both caches.

        Parameters
        ----------
        key: str
        value: Any – JSON‑serialisable.
        embedding: Optional[np.ndarray] – pre‑computed embedding; if omitted a
            deterministic stub is generated.
        """
        self.session.set(key, value, embedding)
        self.project.set(key, value, embedding)

    # ------------------------------------------------------------------- #
    # Retrieval
    # ------------------------------------------------------------------- #
    def get(self, key: str) -> Optional[Any]:
        """Return cached value, checking session first, then project cache."""
        val = self.session.get(key)
        if val is not None:
            return val
        return self.project.get(key)

    # ------------------------------------------------------------------- #
    # Semantic search
    # ------------------------------------------------------------------- #
    def search(
        self, query: str, top_k: int = 5, source: str = "both"
    ) -> List[Tuple[str, Any, float]]:
        """
        Semantic lookup.

        Parameters
        ----------
        query: str
            Text to embed and compare.
        top_k: int
            Maximum number of results.
        source: {"session", "project", "both"}
            Where to perform the search.

        Returns
        -------
        List[Tuple[key, value, similarity]]
        """
        results = []
        if source in ("session", "both"):
            results.extend(self.session.search(query, top_k=top_k))
        if source in ("project", "both"):
            results.extend(self.project.search(query, top_k=top_k))

        # Deduplicate by key, keep highest similarity
        uniq: Dict[str, Tuple[Any, float]] = {}
        for key, val, sim in results:
            if key not in uniq or sim > uniq[key][1]:
                uniq[key] = (val, sim)

        final = [(k, v, s) for k, (v, s) in uniq.items()]
        final.sort(key=lambda x: x[2], reverse=True)
        return final[:top_k]