"""
Project‑level persistent cache.

The cache lives in a SQLite database under ``<workspace>/expert_cache.db``.
Each entry stores:
- ``key``: a deterministic string identifier.
- ``payload``: JSON‑serialised data supplied by the caller.
- ``embedding``: BLOB (list of floats) used for semantic similarity search.
- ``access_count``: integer used for LRU‑style pruning.
- ``last_access``: timestamp for recency weighting.
"""

import json
import os
import sqlite3
import threading
import time
from typing import Any, List, Optional, Tuple

from .embeddings import embed

DB_FILENAME = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "expert_cache.db",
    )
)

_LOCK = threading.RLock()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            embedding BLOB NOT NULL,
            access_count INTEGER NOT NULL DEFAULT 0,
            last_access REAL NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_embedding ON cache (embedding)
        """
    )
    conn.commit()


class ProjectCache:
    """
    Persistent, project‑wide cache with semantic lookup.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_FILENAME
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        with _LOCK:
            _ensure_schema(self._conn)

    def _serialize_embedding(self, vec: List[float]) -> bytes:
        return json.dumps(vec).encode("utf-8")

    def _deserialize_embedding(self, blob: bytes) -> List[float]:
        return json.loads(blob.decode("utf-8"))

    def add(self, key: str, payload: Any, embedding: Optional[List[float]] = None) -> None:
        """
        Insert or replace an entry in the cache.

        Parameters
        ----------
        key:
            Deterministic identifier for the entry.
        payload:
            Any JSON‑serialisable Python object.
        embedding:
            Optional pre‑computed embedding; if omitted the payload is embedded
            automatically via :func:`expert_cache.embeddings.embed`.
        """
        if embedding is None:
            embedding = embed(payload)

        payload_json = json.dumps(payload, ensure_ascii=False)
        now = time.time()
        with _LOCK, self._conn:
            self._conn.execute(
                """
                INSERT INTO cache (key, payload, embedding, access_count, last_access)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(key) DO UPDATE SET
                    payload=excluded.payload,
                    embedding=excluded.embedding,
                    last_access=excluded.last_access
                """,
                (key, payload_json, self._serialize_embedding(embedding), now),
            )

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve an entry by exact key.  Access counters are updated.
        """
        with _LOCK, self._conn:
            cur = self._conn.execute(
                "SELECT payload FROM cache WHERE key = ?", (key,)
            )
            row = cur.fetchone()
            if row is None:
                return None

            # Update access metadata
            self._conn.execute(
                "UPDATE cache SET access_count = access_count + 1, last_access = ? WHERE key = ?",
                (time.time(), key),
            )
            payload_json = row[0]
            return json.loads(payload_json)

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Simple cosine similarity implementation."""
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
        Perform a semantic similarity search over all cached entries.

        Returns a list of ``(key, payload, score)`` tuples sorted by descending
        similarity score.
        """
        with _LOCK, self._conn:
            cur = self._conn.execute("SELECT key, payload, embedding FROM cache")
            results = []
            for key, payload_json, emb_blob in cur:
                emb = self._deserialize_embedding(emb_blob)
                score = self._cosine_similarity(query_embedding, emb)
                if score >= min_score:
                    results.append((key, json.loads(payload_json), score))

        # Sort and keep the top_k
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]

    def prune(self, max_entries: int = 1000) -> None:
        """
        Prune the cache to keep at most ``max_entries`` items.

        Items with low ``access_count`` and older ``last_access`` timestamps are
        removed first.  The pruning score is a weighted sum:
            weight = access_count * 0.7 + (age_seconds) * 0.3
        """
        with _LOCK, self._conn:
            cur = self._conn.execute(
                "SELECT key, access_count, last_access FROM cache"
            )
            now = time.time()
            scored = []
            for key, access_cnt, last_acc in cur:
                age = now - last_acc
                weight = access_cnt * 0.7 + age * 0.3
                scored.append((weight, key))

            scored.sort(reverse=True)  # highest weight = most valuable
            to_keep = set(k for _, k in scored[:max_entries])

            # Delete everything not in the keep‑set
            self._conn.executemany(
                "DELETE FROM cache WHERE key = ?",
                [(k,) for _, k in scored[max_entries:]],
            )
            self._conn.commit()

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with _LOCK:
            self._conn.close()