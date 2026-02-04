"""
worker_pool.py
==============

Parallel task execution with dependency‑aware scheduling.

The pool receives ``Task`` objects that carry a unique ``task_id`` and a list of
``dependencies`` (other task IDs that must finish before this one can run).  Each
worker receives a *minimal* context: the ``Task`` instance itself plus a small
runtime helper (~50 LOC).  The implementation is deliberately lightweight to
keep the worker's memory footprint low.

Groq
----
For inference we use the Groq client (``groq`` package).  The pool does **not**
embed any model logic – it only provides a ``run_inference`` helper that a
task can call.  This keeps the worker sandbox small while still giving fast
hardware acceleration.

Usage
-----
>>> from worker_pool import WorkerPool, Task
>>> pool = WorkerPool(num_workers=4)
>>> tasks = [
...     Task(task_id="a", func=my_func, args=(1,), dependencies=[]),
...     Task(task_id="b", func=my_func, args=(2,), dependencies=["a"]),
... ]
>>> results = pool.execute(tasks)
>>> print(results["b"])
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import os
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Set, Tuple

# --------------------------------------------------------------------------- #
# Optional Groq import – if unavailable we fall back to a dummy stub.
# --------------------------------------------------------------------------- #
try:
    from groq import GroqClient  # type: ignore
except Exception:  # pragma: no cover
    class GroqClient:  # minimal stub
        def __init__(self, *_, **__): ...

        async def infer(self, *_, **__) -> Any:
            raise RuntimeError("Groq client not available")


# --------------------------------------------------------------------------- #
# Logging configuration (lightweight, can be overridden by the host app)
# --------------------------------------------------------------------------- #
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #
@dataclass
class Task:
    """A unit of work.

    Attributes
    ----------
    task_id: Unique identifier.
    func: Callable (sync or async) that performs the work.
    args / kwargs: Parameters passed to ``func``.
    dependencies: List of ``task_id`` strings that must complete before this
        task can start.
    """
    task_id: str
    func: Callable[..., Any] | Callable[..., Awaitable[Any]]
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

    def __hash__(self) -> int:
        return hash(self.task_id)


# --------------------------------------------------------------------------- #
# Helper – tiny runtime context passed to each worker.
# --------------------------------------------------------------------------- #
class _WorkerContext:
    """Minimal context given to a worker.

    Contains:
    - The task itself.
    - A shared Groq client (lazy‑initialized).
    - A tiny helper ``run_inference`` that forwards to Groq.
    """

    __slots__ = ("task", "_groq", "_groq_lock")

    def __init__(self, task: Task, groq_client: GroqClient | None = None):
        self.task = task
        self._groq = groq_client
        self._groq_lock = asyncio.Lock()

    async def _ensure_client(self) -> GroqClient:
        if self._groq is None:
            async with self._groq_lock:
                if self._groq is None:  # double‑checked
                    # In a real deployment the API key would be read from env.
                    api_key = os.getenv("GROQ_API_KEY", "dummy")
                    self._groq = GroqClient(api_key=api_key)
        return self._groq

    async def run_inference(self, *args, **kwargs) -> Any:
        """Thin wrapper around Groq's async inference call."""
        client = await self._ensure_client()
        return await client.infer(*args, **kwargs)


# --------------------------------------------------------------------------- #
# The worker pool
# --------------------------------------------------------------------------- #
class WorkerPool:
    """Dependency‑aware, async‑compatible worker pool.

    Parameters
    ----------
    num_workers: Number of concurrent workers (threads or processes).
    max_queue_size: Upper bound for pending tasks (0 = unlimited).
    """

    def __init__(self, num_workers: int = os.cpu_count() or 4, max_queue_size: int = 0):
        self.num_workers = max(1, num_workers)
        self.max_queue_size = max_queue_size
        self._loop = asyncio.get_event_loop()
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_workers,
            thread_name_prefix="worker-pool"
        )
        # Runtime state
        self._task_map: Dict[str, Task] = {}
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._remaining_deps: Dict[str, int] = {}
        self._ready_queue: asyncio.Queue[Task] = asyncio.Queue(
            maxsize=self.max_queue_size if self.max_queue_size > 0 else 0
        )
        self._results: Dict[str, Any] = {}
        self._exceptions: Dict[str, BaseException] = {}

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    async def execute(self, tasks: Iterable[Task]) -> Dict[str, Any]:
        """Schedule *tasks* respecting their dependencies and return results.

        Returns
        -------
        dict mapping ``task_id`` → result (or raises if any task fails).
        """
        self._reset_state()
        self._populate_graph(tasks)

        # Kick‑off workers
        workers = [
            self._loop.create_task(self._worker_loop(i))
            for i in range(self.num_workers)
        ]

        # Seed the ready queue with tasks that have no dependencies
        for task_id, remaining in self._remaining_deps.items():
            if remaining == 0:
                await self._ready_queue.put(self._task_map[task_id])

        # Wait for completion or failure
        await self._wait_for_completion()

        # Cancel any idle workers
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

        # Propagate first exception if present
        if self._exceptions:
            # Raise the first encountered error with context
            first_key = next(iter(self._exceptions))
            raise RuntimeError(
                f"Task '{first_key}' failed"
            ) from self._exceptions[first_key]

        return self._results

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _reset_state(self) -> None:
        self._task_map.clear()
        self._dependents.clear()
        self._remaining_deps.clear()
        self._results.clear()
        self._exceptions.clear()
        # Drain queue if it held leftovers from a previous run
        while not self._ready_queue.empty():
            self._ready_queue.get_nowait()

    def _populate_graph(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            if task.task_id in self._task_map:
                raise ValueError(f"Duplicate task_id: {task.task_id}")
            self._task_map[task.task_id] = task
            self._remaining_deps[task.task_id] = len(task.dependencies)
            for dep in task.dependencies:
                self._dependents[dep].add(task.task_id)

        # Validate that every dependency exists
        unknown = {
            dep
            for task in self._task_map.values()
            for dep in task.dependencies
            if dep not in self._task_map
        }
        if unknown:
            raise ValueError(f"Undefined dependencies: {unknown}")

    async def _worker_loop(self, worker_id: int) -> None:
        """Continuously pull ready tasks and execute them."""
        LOGGER.debug("Worker %s started", worker_id)
        while True:
            try:
                task = await self._ready_queue.get()
            except asyncio.CancelledError:
                break

            try:
                result = await self._run_task(task)
                self._results[task.task_id] = result
                LOGGER.debug("Task %s completed", task.task_id)
                # Notify dependents
                for dependent in self._dependents.get(task.task_id, []):
                    self._remaining_deps[dependent] -= 1
                    if self._remaining_deps[dependent] == 0:
                        await self._ready_queue.put(self._task_map[dependent])
            except BaseException as exc:  # capture KeyboardInterrupt, etc.
                self._exceptions[task.task_id] = exc
                LOGGER.error("Task %s failed: %s", task.task_id, exc)
                # Propagate failure – workers will still drain the queue but
                # ``execute`` will raise after all are done.
            finally:
                self._ready_queue.task_done()

    async def _run_task(self, task: Task) -> Any:
        """Execute ``task`` inside a minimal context."""
        ctx = _WorkerContext(task)

        # Decide sync vs async
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(ctx, *task.args, **task.kwargs)
        else:
            # Run sync function in thread pool to avoid blocking the event loop
            return await self._loop.run_in_executor(
                self._executor,
                lambda: task.func(ctx, *task.args, **task.kwargs)
            )

    async def _wait_for_completion(self) -> None:
        """Wait until all tasks are done or a failure occurs."""
        total = len(self._task_map)
        while True:
            if len(self._results) + len(self._exceptions) >= total:
                break
            await asyncio.sleep(0.05)  # tiny back‑off


# --------------------------------------------------------------------------- #
# Convenience function for synchronous callers
# --------------------------------------------------------------------------- #
def run_tasks_sync(tasks: Iterable[Task], num_workers: int = 4) -> Dict[str, Any]:
    """Blocking wrapper around :class:`WorkerPool`.

    Example
    -------
    >>> results = run_tasks_sync(my_tasks)
    """
    loop = asyncio.get_event_loop()
    pool = WorkerPool(num_workers=num_workers)
    return loop.run_until_complete(pool.execute(tasks))


# --------------------------------------------------------------------------- #
# Example stub (removed in production)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":  # pragma: no cover
    async def demo_task(ctx: _WorkerContext, value: int) -> int:
        # Simulate a cheap Groq call (replace with real inference)
        await asyncio.sleep(0.1)
        return value * 2

    demo_tasks = [
        Task(task_id="t1", func=demo_task, args=(1,), dependencies=[]),
        Task(task_id="t2", func=demo_task, args=(2,), dependencies=["t1"]),
        Task(task_id="t3", func=demo_task, args=(3,), dependencies=["t1"]),
        Task(task_id="t4", func=demo_task, args=(4,), dependencies=["t2", "t3"]),
    ]

    pool = WorkerPool(num_workers=2)
    result_map = asyncio.run(pool.execute(demo_tasks))
    print("Results:", result_map)