"""
LRU cache with frequency weighting.

Each entry tracks:
- `last_access`: timestamp of most recent hit
- `access_count`: total number of hits

When pruning, a score = access_count / (now - last_access + 1) is used;
the lowest‑scoring items are evicted until the size constraint is met.
"""

import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Iterable, Tuple

class WeightedLRU:
    def __init__(self, max_items: int = 10_000):
        self.max_items = max_items
        self.store: Dict[Any, Tuple[Any, float, int]] = {}  # key -> (value, last_access, count)

    def _now(self) -> float:
        return time.time()

    def _score(self, last_access: float, count: int) -> float:
        # Higher count & recent access -> higher score (less likely to evict)
        age = self._now() - last_access + 1e-6
        return count / age

    def set(self, key: Any, value: Any) -> None:
        now = self._now()
        if key in self.store:
            _, _, cnt = self.store[key]
            self.store[key] = (value, now, cnt + 1)
        else:
            self.store[key] = (value, now, 1)

        if len(self.store) > self.max_items:
            self.prune()

    def get(self, key: Any) -> Any:
        now = self._now()
        if key not in self.store:
            raise KeyError(key)
        val, _, cnt = self.store[key]
        self.store[key] = (val, now, cnt + 1)
        return val

    def __contains__(self, key: Any) -> bool:
        return key in self.store

    def prune(self) -> None:
        """Evict items with the lowest weighted LRU score."""
        if len(self.store) <= self.max_items:
            return

        # Compute scores for all items
        scores = {k: self._score(last, cnt) for k, (_, last, cnt) in self.store.items()}
        # Sort by ascending score (lowest first)
        sorted_keys = sorted(scores, key=scores.get)
        # Number of items to drop
        to_drop = len(self.store) - self.max_items
        for k in sorted_keys[:to_drop]:
            del self.store[k]

    def items(self) -> Iterable[Tuple[Any, Any]]:
        """Yield (key, value) pairs."""
        for k, (v, _, _) in self.store.items():
            yield k, v

    def clear(self) -> None:
        self.store.clear()