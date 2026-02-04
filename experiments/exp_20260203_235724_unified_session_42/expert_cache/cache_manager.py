"""
Facade that coordinates between the persistent (project‑level) cache and the
session‑level cache.

Typical usage::

    from expert_cache.cache_manager import CacheManager

    cache = CacheManager(project_root=Path.cwd())
    cache.set("my_key", {"answer": 42}, "What is the answer to life?")
    result = cache.get("answer to life?")
    if result:
        key, payload, score = result
        ...

The manager first checks the session cache (fastest) and falls back to the
persistent cache if needed.  Writes are performed to both layers so that the
session cache stays warm for the remainder of the session.
"""

from pathlib import Path
from typing import Any, Optional, Tuple

from .persistent_cache import PersistentCache
from .session_cache import SessionCache


class CacheManager:
    """
    High‑level interface exposing a unified cache API.
    """

    def __init__(
        self,
        project_root: Path,
        persistent_db_name: str = "expert_cache.db",
        persistent_max_entries: int = 10_000,
        session_max_entries: int = 1_000,
        embedding_dim: int = 384,
    ):
        """
        Parameters
        ----------
        project_root: Path
            Root directory of the project; the SQLite DB will be placed under
            ``<project_root>/.cache/``.
        persistent_db_name: str
            Filename for the persistent SQLite DB.
        persistent_max_entries: int
            Upper bound for the persistent cache.
        session_max_entries: int
            Upper bound for the in‑memory session cache.
        embedding_dim: int
            Dimensionality of the embedding vectors used throughout.
        """
        cache_dir = project_root / ".cache"
        db_path = cache_dir / persistent_db_name

        self.persistent = PersistentCache(
            db_path=db_path,
            max_entries=persistent_max_entries,
            embedding_dim=embedding_dim,
        )
        self.session = SessionCache(
            max_entries=session_max_entries,
            embedding_dim=embedding_dim,
        )

    # --------------------------------------------------------------------- #
    # Unified API
    # --------------------------------------------------------------------- #
    def set(self, key: str, payload: Any, text_for_embedding: str) -> None:
        """
        Store *payload* under *key* using the semantic representation of
        *text_for_embedding*.

        The entry is written to both the session cache (ephemeral) and the
        persistent cache (disk‑backed) to keep them in sync.
        """
        self.session.set(key, payload, text_for_embedding)
        self.persistent.set(key, payload, text_for_embedding)

    def get(
        self,
        query_text: str,
        top_k: int = 1,
        min_score: float = 0.7,
    ) -> Optional[Tuple[str, Any, float]]:
        """
        Retrieve the best matching cached entry for *query_text*.

        Lookup order:
        1. Session cache (fastest, most recent)
        2. Persistent cache (fallback)

        Returns ``None`` if no entry meets *min_score*.
        """
        # Try session cache first
        session_result = self.session.get(query_text, top_k=top_k, min_score=min_score)
        if session_result:
            return session_result

        # Fallback to persistent cache
        persistent_result = self.persistent.get(
            query_text, top_k=top_k, min_score=min_score
        )
        if persistent_result:
            # Warm the session cache with the hit for future fast access
            key, payload, _ = persistent_result
            self.session.set(key, payload, query_text)
            return persistent_result

        return None

    # --------------------------------------------------------------------- #
    # Convenience helpers
    # --------------------------------------------------------------------- #
    def clear_session(self) -> None:
        """Empty the in‑memory session cache."""
        self.session = SessionCache(
            max_entries=self.session.max_entries,
            embedding_dim=self.session.embedding_dim,
        )

    def clear_persistent(self) -> None:
        """Delete all entries from the persistent cache."""
        # Re‑initialise the SQLite DB file.
        self.persistent._ensure_db()
        with self.persistent._connect() as conn:
            conn.execute("DELETE FROM cache;")
            conn.commit()