import os
import json
import time
import threading
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Helper: simple embedding stub (replace with real model in production)
# --------------------------------------------------------------------------- #
def embed_text(text: str) -> List[float]:
    """
    Convert a piece of text into a deterministic pseudo‑embedding.
    For a real system plug in a transformer model (e.g., sentence‑transformers).

    The implementation below hashes the string and spreads the bits over a
    fixed‑size vector to keep the module self‑contained.
    """
    import hashlib
    import numpy as np

    # 128‑dimensional deterministic embedding
    dim = 128
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Turn bytes into floats in [0, 1)
    arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32) / 255.0
    # Pad / repeat to reach the desired dimension
    if len(arr) < dim:
        repeats = (dim // len(arr)) + 1
        arr = np.tile(arr, repeats)[:dim]
    return arr.tolist()


# --------------------------------------------------------------------------- #
# Core LRU with frequency weighting
# --------------------------------------------------------------------------- #
class _WeightedLRU:
    """
    LRU cache where each entry tracks:
        - last_access (timestamp)
        - access_count (frequency)

    When pruning, items with low frequency and older timestamps are evicted first.
    """
    def __init__(self, max_items: int = 10_000):
        self.max_items = max_items
        self._store: Dict[str, Any] = {}
        self._access_info: Dict[str, Tuple[float, int]] = {}  # key -> (last_ts, count)
        self._lock = threading.RLock()

    def _score(self, key: str) -> float:
        """Higher score = more valuable, lower = candidate for eviction."""
        last_ts, count = self._access_info.get(key, (0.0, 0))
        # Age factor (seconds) – newer = larger value
        age = time.time() - last_ts
        # Inverse age so newer items have higher score
        age_score = 1.0 / (age + 1e-6)
        # Frequency weight
        freq_score = count
        return age_score * freq_score

    def _prune_if_necessary(self):
        if len(self._store) <= self.max_items:
            return
        # Number of items to drop
        excess = len(self._store) - self.max_items
        # Sort by ascending score (worst first)
        sorted_keys = sorted(self._store.keys(), key=self._score)
        for key in sorted_keys[:excess]:
            del self._store[key]
            del self._access_info[key]

    def get(self, key: str) -> Any:
        with self._lock:
            if key not in self._store:
                raise KeyError(key)
            # Update access info
            ts, cnt = self._access_info[key]
            self._access_info[key] = (time.time(), cnt + 1)
            return self._store[key]

    def set(self, key: str, value: Any):
        with self._lock:
            self._store[key] = value
            self._access_info[key] = (time.time(), 1)
            self._prune_if_necessary()

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def items(self):
        return self._store.items()


# --------------------------------------------------------------------------- #
# Persistent project‑level cache (disk‑backed)
# --------------------------------------------------------------------------- #
class ProjectCache:
    """
    A simple persistent cache stored as a JSON lines file.
    Each entry contains:
        - key (hash of the original query)
        - value (arbitrary JSON‑serialisable payload)
        - embedding (list[float])
        - meta: {last_access, access_count}
    LRU pruning is performed on load and after each insertion.
    """
    _CACHE_DIR = Path("expert_cache_data")
    _CACHE_FILE = _CACHE_DIR / "project_cache.jsonl"

    def __init__(self, max_items: int = 100_000):
        self.max_items = max_items
        self._lock = threading.RLock()
        self._index: Dict[str, Tuple[int, List[float]]] = {}  # key -> (file_offset, embedding)
        self._meta: Dict[str, Tuple[float, int]] = {}        # key -> (last_ts, count)
        self._ensure_storage()
        self._load_index()

    # ------------------------------------------------------------------- #
    # Storage handling
    # ------------------------------------------------------------------- #
    def _ensure_storage(self):
        self._CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._CACHE_FILE.touch(exist_ok=True)

    def _load_index(self):
        """Build in‑memory index from the JSONL file."""
        with self._lock, self._CACHE_FILE.open("r", encoding="utf-8") as f:
            offset = 0
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    key = entry["key"]
                    embedding = entry["embedding"]
                    meta = entry.get("meta", {})
                    self._index[key] = (offset, embedding)
                    self._meta[key] = (
                        meta.get("last_access", time.time()),
                        meta.get("access_count", 1),
                    )
                finally:
                    offset = f.tell()

        # Apply pruning on startup if needed
        if len(self._index) > self.max_items:
            self._prune_excess()

    # ------------------------------------------------------------------- #
    # Core API
    # ------------------------------------------------------------------- #
    def _prune_excess(self):
        """Remove lowest‑scoring entries until we are under max_items."""
        # Compute scores
        scores = {}
        for k, (_, _) in self._index.items():
            ts, cnt = self._meta.get(k, (0.0, 0))
            age = time.time() - ts
            age_score = 1.0 / (age + 1e-6)
            scores[k] = age_score * cnt

        # Sort ascending (worst first)
        sorted_keys = sorted(scores, key=scores.get)
        excess = len(self._index) - self.max_items
        keys_to_drop = set(sorted_keys[:excess])

        # Rewrite file without the dropped keys
        temp_path = self._CACHE_FILE.with_suffix(".tmp")
        with self._CACHE_FILE.open("r", encoding="utf-8") as src, \
                temp_path.open("w", encoding="utf-8") as dst:
            offset = 0
            for line in src:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry["key"] in keys_to_drop:
                    continue
                dst.write(json.dumps(entry) + "\n")
                # update new offset
                self._index[entry["key"]] = (offset, entry["embedding"])
                offset = dst.tell()

        temp_path.replace(self._CACHE_FILE)

        # Clean in‑memory structures
        for k in keys_to_drop:
            self._index.pop(k, None)
            self._meta.pop(k, None)

    def _write_entry(self, key: str, value: Any, embedding: List[float]):
        entry = {
            "key": key,
            "value": value,
            "embedding": embedding,
            "meta": {"last_access": time.time(), "access_count": 1},
        }
        line = json.dumps(entry) + "\n"
        with self._lock, self._CACHE_FILE.open("a", encoding="utf-8") as f:
            offset = f.tell()
            f.write(line)
        self._index[key] = (offset, embedding)
        self._meta[key] = (time.time(), 1)

    def _update_meta(self, key: str):
        ts, cnt = self._meta.get(key, (time.time(), 0))
        self._meta[key] = (time.time(), cnt + 1)
        # Update the line in‑place – for simplicity we rewrite the whole file
        # lazily on next prune or explicit flush. This keeps the implementation
        # lightweight while still providing correct semantics.

    # ------------------------------------------------------------------- #
    # Public methods
    # ------------------------------------------------------------------- #
    def get(self, query: str) -> Any:
        """
        Retrieve a cached value by semantic similarity.
        Returns the value of the best‑matching entry if similarity > 0.8,
        otherwise raises KeyError.
        """
        embedding = embed_text(query)
        best_key, best_score = None, -1.0

        for key, (_, stored_emb) in self._index.items():
            # cosine similarity (fast approximation)
            dot = sum(a * b for a, b in zip(embedding, stored_emb))
            norm_a = sum(a * a for a in embedding) ** 0.5
            norm_b = sum(b * b for b in stored_emb) ** 0.5
            sim = dot / (norm_a * norm_b + 1e-9)
            if sim > best_score:
                best_score = sim
                best_key = key

        if best_key is None or best_score < 0.8:
            raise KeyError(f"No sufficiently similar entry for query: {query}")

        # Load the full entry
        offset, _ = self._index[best_key]
        with self._lock, self._CACHE_FILE.open("r", encoding="utf-8") as f:
            f.seek(offset)
            line = f.readline()
            entry = json.loads(line)
        self._update_meta(best_key)
        return entry["value"]

    def set(self, query: str, value: Any):
        """
        Store a value with semantic key derived from the query.
        If the exact key already exists, it is overwritten.
        """
        key = embed_text(query).__hash__()  # deterministic hash from embedding
        key = str(key)  # JSON keys must be strings
        embedding = embed_text(query)

        # Overwrite handling – simply append a new line; old entry will become
        # unreachable and later pruned.
        self._write_entry(key, value, embedding)

        if len(self._index) > self.max_items:
            self._prune_excess()

    def __contains__(self, query: str) -> bool:
        try:
            self.get(query)
            return True
        except KeyError:
            return False

    def clear(self):
        """Delete all persisted entries."""
        with self._lock:
            self._CACHE_FILE.unlink(missing_ok=True)
            self._CACHE_FILE.touch()
            self._index.clear()
            self._meta.clear()


# --------------------------------------------------------------------------- #
# Session‑level (ephemeral) cache
# --------------------------------------------------------------------------- #
class SessionCache:
    """
    In‑memory cache that lives only for the duration of a Python process.
    Uses the same semantic lookup logic as ProjectCache but stores everything
    in a weighted LRU structure.
    """
    def __init__(self, max_items: int = 5_000):
        self._store = _WeightedLRU(max_items=max_items)

    def get(self, query: str) -> Any:
        embedding = embed_text(query)
        best_key, best_score = None, -1.0

        for key, (value, stored_emb) in self._store.items():
            dot = sum(a * b for a, b in zip(embedding, stored_emb))
            norm_a = sum(a * a for a in embedding) ** 0.5
            norm_b = sum(b * b for b in stored_emb) ** 0.5
            sim = dot / (norm_a * norm_b + 1e-9)
            if sim > best_score:
                best_score = sim
                best_key = key

        if best_key is None or best_score < 0.8:
            raise KeyError(f"No similar entry in session cache for query: {query}")

        # Update LRU metadata
        self._store.get(best_key)  # triggers access bookkeeping
        return self._store._store[best_key][0]  # value part

    def set(self, query: str, value: Any):
        key = embed_text(query).__hash__()
        embedding = embed_text(query)
        # Store tuple (value, embedding)
        self._store.set(str(key), (value, embedding))

    def __contains__(self, query: str) -> bool:
        try:
            self.get(query)
            return True
        except KeyError:
            return False

    def clear(self):
        """Remove all entries from the session cache."""
        self._store = _WeightedLRU(max_items=self._store.max_items)