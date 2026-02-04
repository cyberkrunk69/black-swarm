"""
worker_pool.py
----------------
Dependency‑aware parallel execution pool.

Workers receive only the information required to run a single task
(~50 lines of context).  The pool respects the DAG produced by the
Atomizer and uses Groq for ultra‑fast inference where applicable.

Usage
-----
    from worker_pool import WorkerPool, Task

    # Build tasks (the Atomizer would normally produce this)
    tasks = [
        Task(id="t1", func=my_func, args=(...), kwargs={}),
        Task(id="t2", func=my_other, args=(...), kwargs={}, deps=["t1"]),
        ...
    ]

    pool = WorkerPool(tasks, max_workers=8)
    results = pool.run()
"""

from __future__ import annotations

import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Set, Tuple

# --------------------------------------------------------------------------- #
# Optional: Groq inference client (placeholder – replace with real import)
# --------------------------------------------------------------------------- #
try:
    from groq import Groq  # type: ignore
    _groq_client = Groq()
except Exception:  # pragma: no cover
    _groq_client = None  # Groq not available; fallback to normal execution


class Task:
    """
    Minimal representation of a unit of work.

    Attributes
    ----------
    id: str
        Unique identifier.
    func: Callable
        Callable to execute.
    args: Tuple[Any, ...]
        Positional arguments for ``func``.
    kwargs: Dict[str, Any]
        Keyword arguments for ``func``.
    deps: List[str]
        List of task IDs that must complete before this task may run.
    """

    __slots__ = ("id", "func", "args", "kwargs", "deps")

    def __init__(
        self,
        *,
        id: str,
        func: Callable,
        args: Tuple[Any, ...] = (),
        kwargs: Dict[str, Any] | None = None,
        deps: List[str] | None = None,
    ) -> None:
        self.id = id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.deps = deps or []

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task {self.id} deps={self.deps}>"


class WorkerPool:
    """
    Executes a collection of ``Task`` objects respecting their dependency DAG.

    The pool builds an internal ready‑queue from tasks whose dependencies are
    satisfied.  Workers pull from this queue, run the task (optionally via Groq),
    store the result, and then unblock dependent tasks.
    """

    def __init__(self, tasks: List[Task], max_workers: int = 4):
        self.max_workers = max_workers
        self._tasks_by_id: Dict[str, Task] = {t.id: t for t in tasks}
        self._dependents: Dict[str, Set[str]] = {}
        self._remaining_deps: Dict[str, int] = {}
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._ready_queue: queue.Queue[Task] = queue.Queue()

        self._build_dependency_maps()

    # --------------------------------------------------------------------- #
    # Dependency graph preparation
    # --------------------------------------------------------------------- #
    def _build_dependency_maps(self) -> None:
        """
        Populate ``_dependents`` (reverse edges) and ``_remaining_deps``.
        Enqueue tasks that have no dependencies.
        """
        for task in self._tasks_by_id.values():
            self._remaining_deps[task.id] = len(task.deps)
            for dep in task.deps:
                self._dependents.setdefault(dep, set()).add(task.id)

        for task_id, count in self._remaining_deps.items():
            if count == 0:
                self._ready_queue.put(self._tasks_by_id[task_id])

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> Dict[str, Any]:
        """
        Block until all tasks are finished and return a mapping
        ``task_id -> result``.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Keep a set of futures to know when the pool is idle.
            futures = set()

            while True:
                # Pull as many ready tasks as we have workers.
                while not self._ready_queue.empty() and len(futures) < self.max_workers:
                    task = self._ready_queue.get()
                    future = executor.submit(self._execute_task, task)
                    futures.add(future)

                if not futures:
                    # No pending work and no queued tasks → done.
                    break

                # Wait for any future to complete.
                done, _ = threading.Event().wait(0.01), None  # tiny sleep to avoid busy loop
                for future in list(futures):
                    if future.done():
                        futures.remove(future)
                        # Exceptions are propagated to the caller.
                        future.result()

        return self._results

    # --------------------------------------------------------------------- #
    # Worker logic (minimal context)
    # --------------------------------------------------------------------- #
    def _execute_task(self, task: Task) -> None:
        """
        Run a single task, store its result, and unblock dependents.

        This method is intentionally small (≈ 30 lines) to keep the worker
        context minimal.
        """
        # 1️⃣ Run the actual work.  If Groq is available and the task is marked
        #    for fast inference, we could route the call through it.  For now we
        #    simply call the function directly.
        if _groq_client and getattr(task.func, "_use_groq", False):
            # Placeholder: actual Groq integration depends on the SDK.
            result = _groq_client.run(task.func, *task.args, **task.kwargs)  # type: ignore
        else:
            result = task.func(*task.args, **task.kwargs)

        # 2️⃣ Store the result in a thread‑safe manner.
        with self._lock:
            self._results[task.id] = result

            # 3️⃣ Decrease dependency counters of dependents.
            for dependent_id in self._dependents.get(task.id, []):
                self._remaining_deps[dependent_id] -= 1
                if self._remaining_deps[dependent_id] == 0:
                    dependent_task = self._tasks_by_id[dependent_id]
                    self._ready_queue.put(dependent_task)

    # --------------------------------------------------------------------- #
    # Helper for external inspection (optional)
    # --------------------------------------------------------------------- #
    def get_result(self, task_id: str) -> Any:
        """Return the result for *task_id* (raises KeyError if not completed)."""
        return self._results[task_id]

# --------------------------------------------------------------------------- #
# Example stub for Groq‑aware function annotation
# --------------------------------------------------------------------------- #
def groq_enabled(func: Callable) -> Callable:
    """Decorator to flag a function as Groq‑compatible."""
    setattr(func, "_use_groq", True)
    return func

# --------------------------------------------------------------------------- #
# If this file is executed directly, run a tiny demo (useful for quick tests)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    import time

    def slow_add(a, b):
        time.sleep(0.2)
        return a + b

    @groq_enabled
    def fast_mul(a, b):
        # In real life this would be off‑loaded to Groq.
        return a * b

    demo_tasks = [
        Task(id="t1", func=slow_add, args=(1, 2)),
        Task(id="t2", func=fast_mul, args=(3, 4), deps=["t1"]),
        Task(id="t3", func=slow_add, args=(5, 6), deps=["t1"]),
        Task(id="t4", func=fast_mul, args=(7, 8), deps=["t2", "t3"]),
    ]

    pool = WorkerPool(demo_tasks, max_workers=2)
    results = pool.run()
    print("Demo results:", results)