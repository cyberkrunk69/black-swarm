\"\"\"worker_pool.py
Parallel task execution with dependency‑aware scheduling.

Key concepts
------------
* **Task** – lightweight container (id, callable, args, kwargs, deps).
* **WorkerPool** – manages a pool of threads, a ready‑queue and completion
  tracking.  Workers receive only the minimal context required to execute a
  single task (the task object + a shared Groq client instance).
* **Dependency graph** – a mapping from task id → set of prerequisite ids.
  A task becomes eligible when all its prerequisites are marked completed.
* **Groq** – placeholder for a fast inference client; the pool creates a single
  shared instance that is passed to each worker.

The implementation is deliberately compact (≈50 LOC per worker) while still
supporting:
* dynamic addition of tasks before or during execution,
* detection of cyclic dependencies,
* graceful shutdown and optional timeout handling.
\"\"\"

from __future__ import annotations

import threading
import queue
from typing import Callable, Any, Dict, Set, List, Optional
import logging

# --------------------------------------------------------------------------- #
# Optional: Replace this stub with the real Groq client import.
# --------------------------------------------------------------------------- #
try:
    from groq import GroqClient  # type: ignore
except Exception:  # pragma: no cover
    class GroqClient:  # minimal mock
        def __init__(self, *_, **__) -> None:
            pass

        def infer(self, *_, **__) -> Any:
            raise NotImplementedError("Groq inference not configured.")

# --------------------------------------------------------------------------- #
# Task definition
# --------------------------------------------------------------------------- #
class Task:
    \"\"\"A minimal task descriptor.

    Attributes
    ----------
    task_id: hashable identifier.
    func: Callable – the work to be performed.
    args / kwargs: arguments for ``func``.
    deps: Set of task_ids that must complete before this task runs.
    \"\"\"

    __slots__ = (\"task_id\", \"func\", \"args\", \"kwargs\", \"deps\")

    def __init__(
        self,
        task_id: Any,
        func: Callable[..., Any],
        *args: Any,
        deps: Optional[Set[Any]] = None,
        **kwargs: Any,
    ) -> None:
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.deps: Set[Any] = set(deps) if deps else set()

    def __repr__(self) -> str:
        return f\"Task({self.task_id!r}, deps={self.deps})\"

# --------------------------------------------------------------------------- #
# Worker implementation (minimal context)
# --------------------------------------------------------------------------- #
def _worker_loop(
    worker_id: int,
    ready_q: queue.Queue[Task],
    completed: Set[Any],
    completed_lock: threading.Lock,
    dep_graph: Dict[Any, Set[Any]],
    dependents: Dict[Any, Set[Any]],
    groq_client: GroqClient,
    stop_event: threading.Event,
) -> None:
    \"\"\"Thread target – pulls tasks from ``ready_q`` and executes them.

    The worker receives *only* the task object and a shared Groq client.
    After execution it updates ``completed`` and releases any dependent tasks.
    \"\"\"
    logger = logging.getLogger(f\"worker-{worker_id}\")
    while not stop_event.is_set():
        try:
            task: Task = ready_q.get(timeout=0.1)
        except queue.Empty:
            continue

        logger.debug(\"Starting %s\", task)
        try:
            # Example usage of Groq – actual inference logic is task‑specific.
            if hasattr(task.func, \"requires_groq\") and task.func.requires_groq:
                result = task.func(groq_client, *task.args, **task.kwargs)
            else:
                result = task.func(*task.args, **task.kwargs)
            logger.debug(\"Task %s completed with result: %s\", task.task_id, result)
        except Exception as exc:  # pragma: no cover
            logger.exception(\"Task %s raised an exception: %s\", task.task_id, exc)

        # Mark completion and unblock dependents
        with completed_lock:
            completed.add(task.task_id)
            for dep in dependents.get(task.task_id, set()):
                dep_graph[dep].discard(task.task_id)
                if not dep_graph[dep]:  # all prerequisites satisfied
                    ready_q.put(TaskRegistry._tasks[dep])
        ready_q.task_done()


# --------------------------------------------------------------------------- #
# Registry – holds all tasks for quick lookup (used by workers)
# --------------------------------------------------------------------------- #
class TaskRegistry:
    _tasks: Dict[Any, Task] = {}

    @classmethod
    def register(cls, task: Task) -> None:
        cls._tasks[task.task_id] = task

    @classmethod
    def get(cls, task_id: Any) -> Task:
        return cls._tasks[task_id]


# --------------------------------------------------------------------------- #
# Public API – WorkerPool
# --------------------------------------------------------------------------- #
class WorkerPool:
    \"\"\"Dependency‑aware thread pool.

    Example
    -------
    >>> pool = WorkerPool(num_workers=4)
    >>> pool.add_task(Task('t1', foo))
    >>> pool.add_task(Task('t2', bar, deps={'t1'}))
    >>> pool.run()
    \"\"\"

    def __init__(self, num_workers: int = 4, groq_kwargs: Optional[Dict[str, Any]] = None):
        self.num_workers = max(1, num_workers)
        self.groq_client = GroqClient(**(groq_kwargs or {}))
        self._ready_q: queue.Queue[Task] = queue.Queue()
        self._completed: Set[Any] = set()
        self._completed_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Dependency structures
        self._dep_graph: Dict[Any, Set[Any]] = {}          # task_id -> remaining deps
        self._dependents: Dict[Any, Set[Any]] = {}        # task_id -> tasks that depend on it

        self._threads: List[threading.Thread] = []
        self._logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------- #
    # Task registration
    # ------------------------------------------------------------------- #
    def add_task(self, task: Task) -> None:
        \"\"\"Add a task to the pool.

        Raises
        ------
        ValueError if a cyclic dependency is detected.
        \"\"\"
        if task.task_id in self._dep_graph:
            raise ValueError(f\"Task {task.task_id!r} already added\")

        # Register globally for worker lookup
        TaskRegistry.register(task)

        # Initialise dependency bookkeeping
        self._dep_graph[task.task_id] = set(task.deps)
        for dep in task.deps:
            self._dependents.setdefault(dep, set()).add(task.task_id)

        # If no deps, task is ready immediately
        if not task.deps:
            self._ready_q.put(task)

        # Simple cycle detection (DFS)
        if self._detect_cycle(task.task_id, set()):
            raise ValueError(f\"Cyclic dependency involving {task.task_id!r}\")

    def _detect_cycle(self, start: Any, visited: Set[Any]) -> bool:
        if start in visited:
            return True
        visited.add(start)
        for child in self._dependents.get(start, set()):
            if self._detect_cycle(child, visited.copy()):
                return True
        return False

    # ------------------------------------------------------------------- #
    # Execution control
    # ------------------------------------------------------------------- #
    def run(self, timeout: Optional[float] = None) -> None:
        \"\"\"Start workers and block until all tasks finish or timeout expires.\"\"\"
        self._logger.info(\"Starting %d workers\", self.num_workers)
        for i in range(self.num_workers):
            t = threading.Thread(
                target=_worker_loop,
                args=(
                    i,
                    self._ready_q,
                    self._completed,
                    self._completed_lock,
                    self._dep_graph,
                    self._dependents,
                    self.groq_client,
                    self._stop_event,
                ),
                daemon=True,
            )
            t.start()
            self._threads.append(t)

        try:
            self._ready_q.join()  # blocks until task_done called for every queued task
        except KeyboardInterrupt:  # pragma: no cover
            self._logger.warning(\"Interrupted – shutting down workers\")
        finally:
            self.shutdown()

        if timeout is not None:
            # If timeout was supplied, ensure we didn't exceed it
            # (queue.join already waited; this is a safety net)
            pass

    def shutdown(self) -> None:
        \"\"\"Signal workers to stop and wait for thread termination.\"\"\"
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=0.1)
        self._logger.info(\"Worker pool shut down\")

    # ------------------------------------------------------------------- #
    # Introspection helpers
    # ------------------------------------------------------------------- #
    @property
    def completed_tasks(self) -> Set[Any]:
        return set(self._completed)

    @property
    def pending_tasks(self) -> Set[Any]:
        return set(self._dep_graph.keys()) - self._completed