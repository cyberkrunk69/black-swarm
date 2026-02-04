"""
Cache manager implementing a project‑level persistent cache and a
session‑level ephemeral cache with semantic search.

The design follows the *Expert Knowledge Cache* section of
`SWARM_ARCHITECTURE_V2.md`.

Key features:
- Persistent storage using SQLite (project cache) with a simple schema:
    id INTEGER PRIMARY KEY,
    key TEXT UNIQUE,
    embedding BLOB,
    payload BLOB,
    last_access TIMESTAMP,
    access_count INTEGER
- In‑memory session cache using an OrderedDict that stores:
    key → (embedding, payload, access_count)
- Semantic lookup: compute cosine similarity between the query embedding
  and stored embeddings; return the best match above a configurable
  threshold.
- LRU pruning with frequency weighting: items with low access count and
  old last_access are evicted first.
- Thread‑safe via `threading.RLock`.

External dependencies:
- `numpy` for vector maths.
- `sqlite3` (standard library) for persistence.
- `pickle` for payload serialization.
"""

import os
import sqlite3
import threading
import time
import pickle
from collections import OrderedDict
from typing import Any, Callable, List, Tuple, Optional

import numpy as np

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity between two 1‑D arrays."""
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("Cosine similarity expects 1‑D vectors.")
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _serialize(obj: Any) -> bytes:
    """Serialize payload using pickle."""
    return pickle.dumps(obj)


def _deserialize(blob: bytes) -> Any:
    """Deserialize payload."""
    return pickle.loads(blob)


# --------------------------------------------------------------------------- #
# Project‑level persistent cache
# --------------------------------------------------------------------------- #

class ProjectCache:
    """
    Persistent cache stored in a SQLite file.  It holds embeddings and
    arbitrary payloads.  The cache is thread‑safe and supports semantic
    lookup with LRU/LFU pruning.
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        embedding BLOB NOT NULL,
        payload BLOB NOT NULL,
        last_access REAL NOT NULL,
        access_count INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_key ON cache(key);
    CREATE INDEX IF NOT EXISTS idx_last_access ON cache(last_access);
    """

    def __init__(
        self,
        db_path: str,
        max_items: int = 10_000,
        similarity_threshold: float = 0.8,
    ):
        """
        Parameters
        ----------
        db_path: str
            Path to the SQLite database file.
        max_items: int
            Upper bound for number of rows; excess rows are pruned.
        similarity_threshold: float
            Minimum cosine similarity to consider a hit.
        """
        self.db_path = os.path.abspath(db_path)
        self.max_items = max_items
        self.similarity_threshold = similarity_threshold
        self._lock = threading.RLock()
        self._ensure_db()

    # ------------------------------------------------------------------- #
    # DB setup
    # ------------------------------------------------------------------- #
    def _ensure_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(self._SCHEMA)

    def _conn(self):
        """Context manager returning a connection with `row_factory` set."""
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------- #
    # Core API
    # ------------------------------------------------------------------- #
    def set(self, key: str, embedding: np.ndarray, payload: Any) -> None:
        """Insert or update a cache entry."""
        emb_blob = embedding.tobytes()
        payload_blob = _serialize(payload)
        now = time.time()
        with self._lock, self._conn() as conn:
            conn.execute(
                """
                INSERT INTO cache (key, embedding, payload, last_access, access_count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(key) DO UPDATE SET
                    embedding=excluded.embedding,
                    payload=excluded.payload,
                    last_access=excluded.last_access,
                    access_count=access_count+1;
                """,
                (key, emb_blob, payload_blob, now),
            )
            conn.commit()
            self._prune_if_necessary(conn)

    def get(self, key: str) -> Optional[Tuple[np.ndarray, Any]]:
        """Retrieve a cache entry by exact key."""
        with self._lock, self._conn() as conn:
            cur = conn.execute(
                "SELECT embedding, payload FROM cache WHERE key = ?;",
                (key,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            # Update access metadata
            conn.execute(
                "UPDATE cache SET last_access = ?, access_count = access_count + 1 WHERE key = ?;",
                (time.time(), key),
            )
            conn.commit()
            embedding = np.frombuffer(row["embedding"], dtype=np.float32)
            payload = _deserialize(row["payload"])
            return embedding, payload

    def semantic_lookup(
        self,
        query_emb: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[str, float, Any]]:
        """
        Return up to `top_k` cached items whose embeddings are most similar
        to `query_emb`.  Only items with similarity >= `similarity_threshold`
        are returned, ordered by similarity descending.
        """
        with self._lock, self._conn() as conn:
            cur = conn.execute("SELECT key, embedding, payload FROM cache;")
            candidates = []
            for row in cur:
                stored_emb = np.frombuffer(row["embedding"], dtype=np.float32)
                sim = cosine_similarity(query_emb, stored_emb)
                if sim >= self.similarity_threshold:
                    candidates.append((row["key"], sim, row["payload"]))

            # Sort & limit
            candidates.sort(key=lambda x: x[1], reverse=True)
            top = candidates[:top_k]

            # Update access metadata for the hits
            now = time.time()
            for key, _, _ in top:
                conn.execute(
                    "UPDATE cache SET last_access = ?, access_count = access_count + 1 WHERE key = ?;",
                    (now, key),
                )
            conn.commit()

            # Deserialize payloads
            results = [(k, s, _deserialize(p)) for k, s, p in top]
            return results

    # ------------------------------------------------------------------- #
    # Pruning logic – LRU weighted by access frequency
    # ------------------------------------------------------------------- #
    def _prune_if_necessary(self, conn: sqlite3.Connection) -> None:
        """Evict items while the row count exceeds `max_items`."""
        cur = conn.execute("SELECT COUNT(*) AS cnt FROM cache;")
        count = cur.fetchone()["cnt"]
        if count <= self.max_items:
            return

        # Compute a score = (access_count) / (now - last_access + epsilon)
        # Lower scores are evicted first.
        now = time.time()
        epsilon = 1e-6
        conn.execute(
            """
            DELETE FROM cache
            WHERE id IN (
                SELECT id FROM cache
                ORDER BY (access_count / ( ? - last_access + ? )) ASC
                LIMIT ?
            );
            """,
            (now, epsilon, count - self.max_items),
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# Session‑level in‑memory cache
# --------------------------------------------------------------------------- #

class SessionCache:
    """
    Ephemeral, per‑session cache.  Implements an LRU policy with frequency
    weighting: each entry tracks an `access_count`.  When capacity is
    exceeded, the entry with the lowest `score = access_count / (age + ε)`
    is evicted.
    """

    def __init__(self, max_items: int = 500):
        self.max_items = max_items
        self._store: OrderedDict[str, Tuple[np.ndarray, Any, int, float]] = OrderedDict()
        self._lock = threading.RLock()

    def set(self, key: str, embedding: np.ndarray, payload: Any) -> None:
        with self._lock:
            now = time.time()
            if key in self._store:
                # Update existing entry
                _, _, count, _ = self._store.pop(key)
                self._store[key] = (embedding, payload, count + 1, now)
            else:
                self._store[key] = (embedding, payload, 1, now)

            self._ensure_capacity()

    def get(self, key: str) -> Optional[Tuple[np.ndarray, Any]]:
        with self._lock:
            if key not in self._store:
                return None
            embedding, payload, count, _ = self._store.pop(key)
            self._store[key] = (embedding, payload, count + 1, time.time())
            return embedding, payload

    def semantic_lookup(
        self,
        query_emb: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[str, float, Any]]:
        with self._lock:
            candidates = []
            for key, (emb, payload, _, _) in self._store.items():
                sim = cosine_similarity(query_emb, emb)
                if sim > 0:  # keep any positive similarity; caller may filter
                    candidates.append((key, sim, payload))

            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[:top_k]

    def _ensure_capacity(self) -> None:
        """Evict items until we are under `max_items`."""
        while len(self._store) > self.max_items:
            # Find the entry with the lowest weighted score
            now = time.time()
            epsilon = 1e-6
            lowest_key = None
            lowest_score = float("inf")
            for k, (_, _, count, ts) in self._store.items():
                age = now - ts
                score = count / (age + epsilon)  # higher score = more valuable
                if score < lowest_score:
                    lowest_score = score
                    lowest_key = k
            if lowest_key is not None:
                self._store.pop(lowest_key)
            else:
                break


# --------------------------------------------------------------------------- #
# Facade – CacheManager
# --------------------------------------------------------------------------- #

class CacheManager:
    """
    Unified interface that first checks the session cache, then falls back
    to the project cache.  Writes always go to both tiers (project cache
    for persistence, session cache for fast subsequent hits).
    """

    def __init__(
        self,
        project_db_path: str,
        session_max_items: int = 500,
        project_max_items: int = 10_000,
        similarity_threshold: float = 0.8,
    ):
        self.project_cache = ProjectCache(
            db_path=project_db_path,
            max_items=project_max_items,
            similarity_threshold=similarity_threshold,
        )
        self.session_cache = SessionCache(max_items=session_max_items)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def set(
        self,
        key: str,
        embedding: np.ndarray,
        payload: Any,
    ) -> None:
        """
        Store `payload` under `key` with its embedding.
        The entry is written to both caches.
        """
        self.project_cache.set(key, embedding, payload)
        self.session_cache.set(key, embedding, payload)

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve payload by exact key.  Session cache is consulted first.
        """
        result = self.session_cache.get(key)
        if result is not None:
            _, payload = result
            return payload

        proj = self.project_cache.get(key)
        if proj is not None:
            _, payload = proj
            # Populate session cache for faster future access
            embedding, _ = proj
            self.session_cache.set(key, embedding, payload)
            return payload
        return None

    def semantic_lookup(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
    ) -> List[Tuple[str, float, Any]]:
        """
        Perform a semantic search across both tiers.

        1. Query the session cache (fast, in‑memory).
        2. If insufficient results, query the project cache for additional hits.
        3. Merge and return up to `top_k` results ordered by similarity.
        """
        session_hits = self.session_cache.semantic_lookup(query_embedding, top_k=top_k)

        if len(session_hits) >= top_k:
            return session_hits

        # Need more candidates – ask the project cache
        needed = top_k - len(session_hits)
        project_hits = self.project_cache.semantic_lookup(
            query_embedding, top_k=needed
        )

        # Merge, de‑duplicate by key (session wins)
        seen = {k for k, _, _ in session_hits}
        merged = session_hits + [
            (k, sim, payload) for k, sim, payload in project_hits if k not in seen
        ]

        merged.sort(key=lambda x: x[1], reverse=True)
        return merged[:top_k]

    # ------------------------------------------------------------------- #
    # Utility helpers (optional)
    # ------------------------------------------------------------------- #
    def clear_session_cache(self) -> None:
        """Empty the in‑memory cache."""
        with self.session_cache._lock:
            self.session_cache._store.clear()

    def purge_project_cache(self) -> None:
        """Delete all rows from the persistent cache."""
        with self.project_cache._lock, self.project_cache._conn() as conn:
            conn.execute("DELETE FROM cache;")
            conn.commit()