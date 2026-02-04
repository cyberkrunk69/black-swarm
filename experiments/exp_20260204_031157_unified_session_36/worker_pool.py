\"\"\"worker_pool.py
Parallel task execution with dependency‑aware scheduling.

Key concepts
------------
* **Task** – a lightweight container holding a callable, its arguments,
  a unique identifier and a list of prerequisite task ids.
* **WorkerPool** – orchestrates a pool of workers (threads) that pull ready
  tasks from a queue, execute them with a *minimal* context (≈50 LOC) and
  report completion.
* **Dependency graph** – derived from the Atomizer output; a task becomes
  eligible only when all its dependencies have finished.
* **Groq integration** – optional fast inference path; if a task specifies
  ``use_groq=True`` the pool will route the call through the Groq SDK.

The implementation is deliberately compact (≈120 LOC) while still
providing clear separation of concerns and extensibility.
\"\"\"

from __future__ import annotations

import threading
import queue
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple, Optional

# --------------------------------------------------------------------------- #
# Optional Groq support – import lazily to avoid hard dependency.
# --------------------------------------------------------------------------- #
try:
    import groq  # type: ignore
    _GROQ_AVAILABLE = True
except Exception:  # pragma: no cover
    _GROQ_AVAILABLE = False


class Task:
    \"\"\"A minimal representation of a unit of work.\"

    Attributes
    ----------
    tid: str
        Unique identifier.
    fn: Callable[..., Any]
        The callable to execute.
    args: Tuple[Any, ...]
        Positional arguments for ``fn``.
    kwargs: Dict[str, Any]
        Keyword arguments for ``fn``.
    deps: Set[str]
        Set of task ids that must complete before this task runs.
    use_groq: bool
        If True, the task will be executed via the Groq SDK (when available).
    \"\"\"

    __slots__ = (\"tid\", \"fn\", \"args\", \"kwargs\", \"deps\", \"use_groq\")

    def __init__(
        self,
        fn: Callable[..., Any],
        *args: Any,
        deps: Optional[Iterable[str]] = None,
        use_groq: bool = False,
        **kwargs: Any,
    ) -> None:
        self.tid: str = str(uuid.uuid4())
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.deps: Set[str] = set(deps) if deps else set()
        self.use_groq = use_groq

    def is_ready(self, completed: Set[str]) -> bool:
        \"\"\"Return ``True`` if all dependencies are satisfied.\"\"\"
        return self.deps.issubset(completed)


# --------------------------------------------------------------------------- #
# WorkerPool – core scheduler
# --------------------------------------------------------------------------- #
class WorkerPool:
    \"\"\"Execute ``Task`` objects respecting dependencies.

    The pool maintains:
    * ``_tasks`` – mapping ``tid → Task`` for lookup.
    * ``_ready_q`` – thread‑safe queue of tasks whose deps are satisfied.
    * ``_completed`` – set of finished task ids.
    * ``_lock`` – protects shared state during dependency updates.
    * ``_executor`` – underlying thread pool (configurable size).

    Example
    -------
    >>> def work(x): return x * x
    >>> pool = WorkerPool(max_workers=4)
    >>> t1 = pool.add_task(work, 2)
    >>> t2 = pool.add_task(work, 3, deps=[t1.tid])
    >>> results = pool.run()
    >>> results[t2.tid]
    9
    \"\"\"

    def __init__(self, max_workers: int = 4) -> None:
        self._tasks: Dict[str, Task] = {}
        self._ready_q: queue.Queue[Task] = queue.Queue()
        self._completed: Set[str] = set()
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def add_task(
        self,
        fn: Callable[..., Any],
        *args: Any,
        deps: Optional[Iterable[str]] = None,
        use_groq: bool = False,
        **kwargs: Any,
    ) -> Task:
        \"\"\"Create a ``Task`` and register it with the pool.\n\n        The task is *not* scheduled yet; ``run`` will evaluate the
        dependency graph and populate the ready queue.\n        \"\"\"
        task = Task(fn, *args, deps=deps, use_groq=use_groq, **kwargs)
        with self._lock:
            self._tasks[task.tid] = task
        return task

    def run(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        \"\"\"Execute all registered tasks and return a ``tid → result`` map.\n\n        ``timeout`` propagates to ``ThreadPoolExecutor.shutdown``.\n        \"\"\"
        # Seed the ready queue with tasks that have no unmet deps.
        with self._lock:
            for task in self._tasks.values():
                if not task.deps:
                    self._ready_q.put(task)

        # Submit workers – each worker pulls from the queue until empty.
        futures = [
            self._executor.submit(self._worker_loop) for _ in range(self._executor._max_workers)
        ]

        # Wait for completion.
        for f in futures:
            f.result(timeout=timeout)  # re‑raise any exception

        self._executor.shutdown(wait=True, cancel_futures=False)
        return dict(self._results)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    def _worker_loop(self) -> None:
        \"\"\"Continuously fetch tasks from ``_ready_q`` and execute them.\n\n        The loop terminates when the queue is empty *and* all tasks are
        marked completed.\n        \"\"\"
        while True:
            try:
                task: Task = self._ready_q.get_nowait()
            except queue.Empty:
                # No more ready tasks – verify termination condition.
                with self._lock:
                    if len(self._completed) == len(self._tasks):
                        break
                # Small spin‑wait to allow other workers to enqueue new tasks.
                continue

            try:
                result = self._execute_task(task)
                with self._lock:
                    self._results[task.tid] = result
                    self._completed.add(task.tid)
                    self._propagate_ready(task.tid)
            finally:
                self._ready_q.task_done()

    def _execute_task(self, task: Task) -> Any:
        \"\"\"Run ``task`` with either normal Python call or Groq inference.\n\n        The *minimal* context passed to the worker is the callable itself and
        its arguments – roughly 50 lines of code total.\n        \"\"\"
        if task.use_groq and _GROQ_AVAILABLE:
            # Very thin wrapper around Groq SDK – replace with actual API as needed.
            client = groq.GroqClient()
            # Assume ``fn`` is a string identifier understood by Groq; we pass args as payload.
            payload = {\"args\": task.args, \"kwargs\": task.kwargs}
            return client.run(task.fn.__name__, payload)
        else:
            return task.fn(*task.args, **task.kwargs)

    def _propagate_ready(self, finished_tid: str) -> None:
        \"\"\"Enqueue any tasks that become ready after ``finished_tid`` completes.\"\"\"
        for candidate in self._tasks.values():
            if candidate.tid in self._completed:
                continue
            if finished_tid in candidate.deps:
                candidate.deps.remove(finished_tid)
            if not candidate.deps:
                self._ready_q.put(candidate)


# --------------------------------------------------------------------------- #
# Convenience function for one‑off usage
# --------------------------------------------------------------------------- #
def run_tasks(
    tasks: Iterable[Tuple[Callable[..., Any], Tuple[Any, ...], Dict[str, Any], List[str], bool]],
    max_workers: int = 4,
) -> Dict[str, Any]:
    \"\"\"Utility wrapper around :class:`WorkerPool`.\n\n    ``tasks`` is an iterable of tuples:\n        (fn, args, kwargs, deps, use_groq)\n    Returns a mapping of task ids to results.\n    \"\"\"
    pool = WorkerPool(max_workers=max_workers)
    for fn, args, kwargs, deps, use_groq in tasks:
        pool.add_task(fn, *args, deps=deps, use_groq=use_groq, **kwargs)
    return pool.run()


# --------------------------------------------------------------------------- #
# Example (executed only when run as a script)
# --------------------------------------------------------------------------- #
if __name__ == \"__main__\":  # pragma: no cover
    import time

    def demo(x: int) -> int:
        time.sleep(0.1)
        return x * x

    wp = WorkerPool(max_workers=2)
    t_a = wp.add_task(demo, 2)
    t_b = wp.add_task(demo, 3, deps=[t_a.tid])
    t_c = wp.add_task(demo, 4, deps=[t_a.tid])
    t_d = wp.add_task(demo, 5, deps=[t_b.tid, t_c.tid])

    results = wp.run()
    for tid, val in results.items():
        print(f\"{tid[:8]} → {val}\")