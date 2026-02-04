"""
expert_cache package initializer.

Exports:
    CacheManager – high‑level interface for project‑level persistent cache
                  and session‑level ephemeral cache with semantic lookup.
"""
from .cache_manager import CacheManager

__all__ = ["CacheManager"]