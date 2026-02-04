import importlib
import threading
from typing import Any

class GrindSpawner:
    """
    Proxy for the real GrindSpawner defined in grind_spawner.py.
    Delays the heavy import/initialisation until the first attribute
    or method is accessed.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._real_spawner = None          # type: ignore
        self._init_args = args
        self._init_kwargs = kwargs
        self._lock = threading.Lock()

    def _ensure_real(self) -> None:
        """Import and instantiate the real GrindSpawner exactly once."""
        if self._real_spawner is None:
            with self._lock:
                if self._real_spawner is None:
                    module = importlib.import_module('grind_spawner')
                    RealSpawner = getattr(module, 'GrindSpawner')
                    self._real_spawner = RealSpawner(*self._init_args, **self._init_kwargs)

    def __getattr__(self, name: str) -> Any:
        """
        Forward attribute access to the real spawner after ensuring it is loaded.
        This method is invoked for any attribute not found on the proxy itself.
        """
        self._ensure_real()
        return getattr(self._real_spawner, name)