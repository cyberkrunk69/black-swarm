"""
dynamic_parallel.py

Utility for determining a dynamic `max_parallel` value for grind_spawner_unified.py and
providing a simple work‑stealing executor for heterogeneous engine pools.

The original grind_spawner_unified.py contains a hard‑coded:

    max_parallel = 4

We cannot edit that file (read‑only), so this module exposes a drop‑in replacement
function `get_dynamic_max_parallel()` and a `WorkStealingExecutor` that can be used
by the caller to schedule tasks across available engines.

Usage example (in a wrapper around grind_spawner_unified):

    from dynamic_parallel import get_dynamic_max_parallel, WorkStealingExecutor
    max_parallel = get_dynamic_max_parallel(task_complexity=task.complexity)
    executor = WorkStealingExecutor(engines, max_parallel)
    results = executor.map(task_func, task_items)

The implementation makes decisions based on:
    * task_complexity – an integer (higher = more CPU/IO heavy)
    * rate limit status – queried via the `rate_limit` module (if present)
    * available engines – list of engine descriptors exposing `capacity` and `speed_factor`

The work‑stealing executor maintains a shared queue and lets faster engines
pull additional work when they become idle.
"""

import threading
import queue
import time
from typing import Callable, Iterable, List, Any, Optional

# ----------------------------------------------------------------------
# Helper functions to introspect rate‑limit status and engine capabilities.
# These are deliberately defensive – if the underlying modules are not
# available we fall back to sensible defaults.
# ----------------------------------------------------------------------


def _current_rate_limit_remaining() -> Optional[int]:
    """
    Attempt to import a hypothetical `rate_limit` module that provides
    `get_remaining_quota()` returning the number of remaining requests.
    Returns None if the module or function is unavailable.
    """
    try:
        import rate_limit  # type: ignore
        return rate_limit.get_remaining_quota()
    except Exception:
        return None


def _engine_speed_factor(engine) -> float:
    """
    Derive a relative speed factor for an engine.
    Expected engine attributes:
        - `capacity` (int): number of concurrent tasks it can handle.
        - `speed_multiplier` (float, optional): empirical speed rating.
    If not present, defaults to 1.0.
    """
    speed = getattr(engine, "speed_multiplier", None)
    if speed is None:
        # fallback: assume capacity correlates with speed
        capacity = getattr(engine, "capacity", 1)
        speed = float(capacity)
    return float(speed)


# ----------------------------------------------------------------------
# Dynamic max_parallel calculation
# ----------------------------------------------------------------------


def get_dynamic_max_parallel(
    task_complexity: int = 1,
    engines: Optional[List[Any]] = None,
    min_parallel: int = 1,
    max_cap: int = 32,
) -> int:
    """
    Compute a dynamic `max_parallel` value.

    Parameters
    ----------
    task_complexity: int
        Rough estimate of how heavy a single task is. Larger numbers imply
        more CPU/IO usage, so we reduce parallelism.
    engines: list, optional
        List of engine objects. If omitted, we assume a single generic engine.
    min_parallel: int
        Lower bound for parallelism.
    max_cap: int
        Upper bound to avoid spawning too many threads.

    Returns
    -------
    int
        The calculated max_parallel value.
    """
    # Base parallelism from engines
    if engines:
        total_capacity = sum(getattr(e, "capacity", 1) for e in engines)
        avg_speed = sum(_engine_speed_factor(e) for e in engines) / len(engines)
    else:
        total_capacity = 1
        avg_speed = 1.0

    # Adjust for task complexity (simple heuristic)
    complexity_factor = max(1, task_complexity)

    # Rate‑limit influence: if quota is low, be conservative
    remaining_quota = _current_rate_limit_remaining()
    if remaining_quota is not None and remaining_quota < 10:
        quota_factor = 0.5
    else:
        quota_factor = 1.0

    # Compute raw parallelism
    raw_parallel = int(total_capacity * avg_speed / complexity_factor * quota_factor)

    # Clamp to allowed bounds
    parallel = max(min_parallel, min(raw_parallel, max_cap))
    return parallel


# ----------------------------------------------------------------------
# Work‑stealing executor
# ----------------------------------------------------------------------


class WorkStealingExecutor:
    """
    Simple thread‑based work‑stealing executor.

    Each engine runs in its own thread (or a pool of threads if the engine
    reports `capacity > 1`). When a thread finishes its current task it
    attempts to steal work from the global queue, ensuring that faster
    engines keep busy.

    The API mirrors `concurrent.futures.Executor.map` for familiarity.
    """

    def __init__(self, engines: List[Any], max_parallel: Optional[int] = None):
        """
        Parameters
        ----------
        engines: list
            Engine objects that expose a callable `run(task)` method.
        max_parallel: int, optional
            Upper bound on total concurrent tasks. If None, we compute a
            dynamic value using the engines list and a default complexity of 1.
        """
        self.engines = engines
        self.max_parallel = (
            max_parallel
            if max_parallel is not None
            else get_dynamic_max_parallel(engines=engines)
        )
        self._task_queue: queue.Queue = queue.Queue()
        self._results: List[Any] = []
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
        self._shutdown = False

    def submit(self, fn: Callable, *args, **kwargs):
        """Enqueue a single callable."""
        self._task_queue.put((fn, args, kwargs))

    def map(self, fn: Callable, iterable: Iterable, timeout: Optional[float] = None) -> List[Any]:
        """
        Schedule `fn(item)` for each item in `iterable` and block until
        all tasks complete (or timeout expires).

        Returns a list of results preserving input order.
        """
        # Preserve order by tagging each item with its index
        indexed_items = list(enumerate(iterable))
        for idx, item in indexed_items:
            self.submit(fn, idx, item)

        # Launch worker threads respecting max_parallel
        self._start_workers()

        # Wait for completion
        start_time = time.time()
        while not self._task_queue.empty() or any(t.is_alive() for t in self._threads):
            if timeout is not None and (time.time() - start_time) > timeout:
                raise TimeoutError("WorkStealingExecutor.map timed out")
            time.sleep(0.01)  # tiny sleep to avoid busy loop

        # Order results by original index
        ordered = [None] * len(indexed_items)
        for idx, result in self._results:
            ordered[idx] = result
        return ordered

    def _worker(self, engine):
        """Worker loop for a single engine."""
        while not self._shutdown:
            try:
                fn, args, kwargs = self._task_queue.get_nowait()
            except queue.Empty:
                break  # No more work
            try:
                # Engines may require a specific call signature; we assume `run`
                if hasattr(engine, "run"):
                    result = engine.run(fn, *args, **kwargs)
                else:
                    # Fallback to direct call
                    result = fn(*args, **kwargs)
                with self._lock:
                    self._results.append((args[0], result))  # args[0] is the index
            finally:
                self._task_queue.task_done()

    def _start_workers(self):
        """Spin up threads up to max_parallel, distributing engines."""
        # Determine how many threads per engine based on its capacity
        total_threads = 0
        for engine in self.engines:
            capacity = getattr(engine, "capacity", 1)
            for _ in range(capacity):
                if total_threads >= self.max_parallel:
                    break
                t = threading.Thread(target=self._worker, args=(engine,), daemon=True)
                t.start()
                self._threads.append(t)
                total_threads += 1
            if total_threads >= self.max_parallel:
                break

    def shutdown(self, wait: bool = True):
        """Signal workers to stop and optionally wait for them."""
        self._shutdown = True
        if wait:
            for t in self._threads:
                t.join()


# ----------------------------------------------------------------------
# Example placeholder (not executed on import)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Mock engine for demonstration
    class MockEngine:
        def __init__(self, capacity=1, speed_multiplier=1.0):
            self.capacity = capacity
            self.speed_multiplier = speed_multiplier

        def run(self, fn, *args, **kwargs):
            # Simulate work
            return fn(*args, **kwargs)

    def sample_task(idx, value):
        time.sleep(0.1)  # pretend work
        return f"Task {idx}: {value * 2}"

    engines = [MockEngine(capacity=2, speed_multiplier=1.5), MockEngine()]
    executor = WorkStealingExecutor(engines)
    results = executor.map(sample_task, range(10))
    print("Results:", results)