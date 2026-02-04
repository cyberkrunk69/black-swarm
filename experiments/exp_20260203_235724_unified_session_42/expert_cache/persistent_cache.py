"""
Project‑level persistent cache.

The cache stores arbitrary JSON‑serialisable payloads together with a dense
embedding vector.  Lookup is performed via cosine similarity on the stored
embeddings.  A lightweight SQLite database is used for durability; the
embeddings themselves are persisted as BLOBs (NumPy ``float32`` arrays).

LRU pruning with frequency weighting:
- Each entry tracks ``last_access`` (timestamp) and ``access_count``.
- When the cache exceeds ``max_entries`` the eviction score is computed as:
      score = (now - last_access) / access_count
  The entry with the highest score is removed.
"""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np

from .embedding_utils import embed_text, batch_embed_texts


class PersistentCache:
    """
    Persistent, project‑wide cache with semantic lookup.
    """

    DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        embedding BLOB NOT NULL,
        last_access REAL NOT NULL,
        access_count INTEGER NOT NULL
    );
    """

    def __init__(
        self,
        db_path: Path,
        max_entries: int = 10_000,
        embedding_dim: int = 384,
    ):
        """
        Parameters
        ----------
        db_path: Path
            Location of the SQLite database file.
        max_entries: int
            Upper bound on number of cached items before pruning.
        embedding_dim: int
            Dimensionality of the stored embeddings.
        """
        self.db_path = db_path
        self.max_entries = max_entries
        self.embedding_dim = embedding_dim

        self._ensure_db()

    # --------------------------------------------------------------------- #
    # SQLite helpers
    # --------------------------------------------------------------------- #
    def _ensure_db(self) -> None:
        os.makedirs(self.db_path.parent, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self.DB_SCHEMA)
            conn.commit()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)

    # --------------------------------------------------------------------- #
    # Core API
    # --------------------------------------------------------------------- #
    def set(self, key: str, payload: Any, text_for_embedding: str) -> None:
        """
        Store *payload* under *key* using the embedding derived from
        *text_for_embedding*.

        The payload must be JSON‑serialisable.
        """
        embedding = embed_text(text_for_embedding, dim=self.embedding_dim)
        blob = embedding.tobytes()
        payload_json = json.dumps(payload, ensure_ascii=False)

        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                (key, payload, embedding, last_access, access_count)
                VALUES (?, ?, ?, ?, COALESCE(
                    (SELECT access_count FROM cache WHERE key = ?), 0) + 1)
                """,
                (key, payload_json, blob, now, key),
            )
            conn.commit()

        self._prune_if_necessary()

    def get(
        self,
        query_text: str,
        top_k: int = 1,
        min_score: float = 0.7,
    ) -> Optional[Tuple[str, Any, float]]:
        """
        Perform a semantic lookup using *query_text*.

        Returns the best match (key, payload, cosine similarity) if the similarity
        exceeds *min_score*.  If no entry meets the threshold, ``None`` is returned.
        """
        query_vec = embed_text(query_text, dim=self.embedding_dim)

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key, payload, embedding, last_access, access_count FROM cache"
            ).fetchall()

        if not rows:
            return None

        # Decode embeddings & compute cosine similarity
        candidates = []
        for key, payload_json, emb_blob, last_access, access_count in rows:
            stored_vec = np.frombuffer(emb_blob, dtype=np.float32)
            # Cosine similarity (vectors are already normalised)
            score = float(np.dot(query_vec, stored_vec))
            if score >= min_score:
                candidates.append((score, key, payload_json, last_access, access_count))

        if not candidates:
            return None

        # Sort by score descending
        candidates.sort(reverse=True, key=lambda x: x[0])
        best_score, best_key, best_payload_json, best_last, best_cnt = candidates[0]

        # Update access metadata
        now = time.time()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE cache
                SET last_access = ?, access_count = access_count + 1
                WHERE key = ?
                """,
                (now, best_key),
            )
            conn.commit()

        payload = json.loads(best_payload_json)
        return best_key, payload, best_score

    # --------------------------------------------------------------------- #
    # Pruning
    # --------------------------------------------------------------------- #
    def _prune_if_necessary(self) -> None:
        """
        Enforce ``max_entries`` using LRU weighted by access frequency.
        """
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            if total <= self.max_entries:
                return

            # Compute eviction score = (now - last_access) / access_count
            now = time.time()
            rows = conn.execute(
                """
                SELECT key, last_access, access_count
                FROM cache
                ORDER BY ((? - last_access) / (access_count + 0.0)) DESC
                LIMIT ?
                """,
                (now, total - self.max_entries),
            ).fetchall()

            keys_to_evict = [row[0] for row in rows]
            conn.executemany("DELETE FROM cache WHERE key = ?", [(k,) for k in keys_to_evict])
            conn.commit()