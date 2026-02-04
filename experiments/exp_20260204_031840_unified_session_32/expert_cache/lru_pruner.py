"""
LRU pruning logic with frequency weighting.

The cache stores, for each key, a tuple:
    (value, embedding, access_count, last_access_timestamp)

When the cache exceeds its capacity, a batch of entries is examined.
Entries with low access frequency are evicted first. Access counts decay
over time to favour recent usage.
"""
import time
from typing import Dict, Tuple, Any, List

from .config import (
    SESSION_CACHE_MAX_ITEMS,
    SESSION_CACHE_PRUNE_BATCH,
    LRU_DECAY_FACTOR,
    LRU_MIN_FREQUENCY,
)


CacheEntry = Tuple[Any, Any, int, float]  # (value, embedding, freq, last_ts)


def _decay_frequencies(entries: List[CacheEntry]) -> List[CacheEntry]:
    """Apply exponential decay to the frequency counters."""
    decayed = []
    for value, emb, freq, ts in entries:
        new_freq = max(int(freq * LRU_DECAY_FACTOR), LRU_MIN_FREQUENCY)
        decayed.append((value, emb, new_freq, ts))
    return decayed


def prune_cache(cache: Dict[str, CacheEntry]) -> None:
    """
    Prune the provided cache dict in‑place.

    The algorithm:
        1. If cache size <= max, do nothing.
        2. Randomly (or by insertion order) select a batch of items.
        3. Decay their frequencies.
        4. Evict the items with the lowest frequency until the cache size
           falls below the configured maximum.
    """
    if len(cache) <= SESSION_CACHE_MAX_ITEMS:
        return

    # Step 2 – pick a slice of items (deterministic by insertion order for reproducibility)
    keys = list(cache.keys())
    batch_keys = keys[: SESSION_CACHE_PRUNE_BATCH]

    # Step 3 – decay frequencies for the batch
    for k in batch_keys:
        value, emb, freq, ts = cache[k]
        new_freq = max(int(freq * LRU_DECAY_FACTOR), LRU_MIN_FREQUENCY)
        cache[k] = (value, emb, new_freq, ts)

    # Step 4 – sort entire cache by frequency (ascending) and evict
    sorted_items = sorted(cache.items(), key=lambda item: item[1][2])  # freq at index 2
    while len(cache) > SESSION_CACHE_MAX_ITEMS and sorted_items:
        evict_key, _ = sorted_items.pop(0)
        del cache[evict_key]