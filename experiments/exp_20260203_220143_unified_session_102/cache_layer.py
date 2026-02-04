\"\"\"Cache layer for frequently accessed resources.

Provides:
* In‑memory key/value store with optional TTL.
* Thread‑safe operations.
* ``@cached`` decorator for functions (uses LRU fallback if no TTL).
\"\"\"

from __future__ import annotations

import functools
import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

_K = TypeVar("_K")
_V = TypeVar("_V")


class TTLCache(Generic[_K, _V]):
    \"\"\"Thread‑safe cache with optional time‑to‑live (TTL).

    Parameters
    ----------
    maxsize: int
        Maximum number of items to store. When exceeded, the oldest
        entry (by insertion order) is evicted.
    ttl: float | None
        Seconds an entry stays valid. ``None`` means entries never expire.
    \"\"\"

    def __init__(self, maxsize: int = 128, ttl: Optional[float] = None) -> None:
        self.maxsize = maxsize
        self.ttl = ttl
        self._store: OrderedDict[_K, tuple[_V, float]] = OrderedDict()
        self._lock = threading.RLock()

    def _now(self) -> float:
        return time.monotonic()

    def _is_expired(self, timestamp: float) -> bool:
        if self.ttl is None:
            return False
        return (self._now() - timestamp) > self.ttl

    def get(self, key: _K, default: Optional[_V] = None) -> Optional[_V]:
        with self._lock:
            if key not in self._store:
                return default
            value, ts = self._store[key]
            if self._is_expired(ts):
                # Expired – remove and return default
                del self._store[key]
                return default
            # Move to end to mark as recently used
            self._store.move_to_end(key)
            return value

    def set(self, key: _K, value: _V) -> None:
        with self._lock:
            if key in self._store:
                # Overwrite – just update value & timestamp
                self._store[key] = (value, self._now())
                self._store.move_to_end(key)
                return

            # Evict if needed
            if len(self._store) >= self.maxsize:
                # pop oldest item
                self._store.popitem(last=False)

            self._store[key] = (value, self._now())

    def delete(self, key: _K) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __contains__(self, key: object) -> bool:
        # ``in`` should respect TTL
        return self.get(key) is not None

    def __len__(self) -> int:
        # Count only non‑expired entries
        with self._lock:
            # Clean up expired items lazily
            keys_to_remove = [k for k, (_, ts) in self._store.items() if self._is_expired(ts)]
            for k in keys_to_remove:
                del self._store[k]
            return len(self._store)


def cached(
    *,
    maxsize: int = 128,
    ttl: Optional[float] = None,
) -> Callable[[Callable[..., _V]], Callable[..., _V]]:
    \"\"\"Function decorator that caches results in a :class:`TTLCache`.

    Example
    -------
    >>> @cached(ttl=60)
    ... def expensive_computation(x):
    ...     print(\"computing...\")
    ...     return x * x
    >>> expensive_computation(2)  # computes
    computing...
    4
    >>> expensive_computation(2)  # cached
    4
    \"\"\"

    cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(func: Callable[..., _V]) -> Callable[..., _V]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> _V:
            # Build a hashable cache key from args & kwargs
            key = (args, frozenset(sorted(kwargs.items())))
            cached_result = cache.get(key)  # type: ignore[arg-type]
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result

        wrapper.cache = cache  # expose for testing / manual invalidation
        return wrapper

    return decorator


# --------------------------------------------------------------------------- #
# Convenience singleton for generic resource caching
# --------------------------------------------------------------------------- #

resource_cache = TTLCache(maxsize=1024, ttl=300)  # 5‑minute default TTL


def get_cached_resource(key: str, loader: Callable[[], Any]) -> Any:
    \"\"\"Retrieve a resource from the global cache or load it.

    Parameters
    ----------
    key: str
        Identifier used for caching.
    loader: Callable[[], Any]
        Callable that returns the resource if it is not cached.

    Returns
    -------
    Any
        Cached or newly loaded resource.
    \"\"\"
    cached = resource_cache.get(key)
    if cached is not None:
        return cached
    # Load, store, and return
    resource = loader()
    resource_cache.set(key, resource)
    return resource