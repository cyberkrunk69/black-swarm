"""
expert_cache package

Provides:
- ProjectCache: persistent, project‑wide cache stored on disk.
- SessionCache: short‑lived, in‑memory cache for the current execution session.
- CacheManager: high‑level façade that combines both caches and performs
  semantic look‑up using vector embeddings.
"""

from .project_cache import ProjectCache
from .session_cache import SessionCache
from .cache_manager import CacheManager

__all__ = ["ProjectCache", "SessionCache", "CacheManager"]