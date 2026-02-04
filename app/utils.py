import importlib
import json
import os
import threading
import time
from functools import wraps
from pathlib import Path

# ----------------------------------------------------------------------
# Lazy import helper
# ----------------------------------------------------------------------
def lazy_import(module_name: str):
    """
    Returns a proxy object that lazily imports the requested module on first attribute access.
    """
    class _LazyModule:
        __module = None

        def _load(self):
            if self.__module is None:
                self.__module = importlib.import_module(module_name)

        def __getattr__(self, item):
            self._load()
            return getattr(self.__module, item)

        def __repr__(self):
            return f"<lazy module '{module_name}'>"

    return _LazyModule()

# ----------------------------------------------------------------------
# Simple disk‑based cache for immutable results
# ----------------------------------------------------------------------
_CACHE_PATH = Path(".spawner_cache.json")
_CACHE_LOCK = threading.Lock()

def _load_cache():
    if _CACHE_PATH.is_file():
        try:
            with _CACHE_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_cache(data):
    with _CACHE_LOCK:
        with _CACHE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def cache_result(key):
    """
    Decorator that caches the function result on disk under the given key.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = _load_cache()
            if key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache[key] = result
            _save_cache(cache)
            return result
        return wrapper
    return decorator

# ----------------------------------------------------------------------
# Background task runner for deferred init steps
# ----------------------------------------------------------------------
def run_deferred_init(init_callable):
    """
    Executes a heavy, non‑critical init function in a background daemon thread.
    """
    thread = threading.Thread(target=init_callable, daemon=True)
    thread.start()
    return thread