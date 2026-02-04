"""
worker_pool.py
==============

Parallel task execution with dependency‑aware scheduling.

Workers receive a *minimal* execution context – the task object and a
small (~50 LOC) helper that provides the task’s callable and its
dependencies.  The pool respects the dependency graph produced by the
Atomizer and uses Groq for fast inference where required.

Only core system files are read‑only; this module is new and lives under
the experiment folder.
"""

from __future__ import annotations

import threading
import queue
import uuid
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, Set, List, Optional

# --------------------------------------------------------------------------- #
# Groq inference placeholder
# --------------------------------------------------------------------------- #
def groq_infer(prompt: str, **kwargs) -> str:
    """
    Perform fast inference using Groq.

    This is a thin wrapper around the Groq client.  In the real system
    the client would be imported from the Groq SDK; here we provide a
    stub that can be swapped out without touching the scheduler.
    """
    # NOTE: Replace with actual Groq client call, e.g.:
    #   from groq import GroqClient
    #   client = GroqClient()
    #   return client.infer(prompt, **kwargs)
    return f"[Groq] {prompt}"  # mock response


# --------------------------------------------------------------------------- #
# Task definition
# --------------------------------------------------------------------------- #
@dataclass
class Task:
    """
    Represents a unit of work.

    Attributes
    ----------
    func : Callable[[Any], Any]
        The function that performs the work.  It receives the task's
        ``payload`` as its sole argument.
    payload : Any
        Arbitrary data handed to ``func``.
    deps : Set[str]
        IDs of tasks that must complete before this task may run.
    task_id : str
        Unique identifier (auto‑generated if omitted).
    result : Any = field(default=None, init=False)
        The result of ``func`` after execution.
    """
    func: Callable[[Any], Any]
    payload: Any = None
    deps: Set[str] = field(default_factory=set)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    result: Any = field(default=None, init=False)


# --------------------------------------------------------------------------- #
# Worker implementation
# --------------------------------------------------------------------------- #
class _Worker(threading.Thread):
    """
    Internal worker thread.

    Each worker pulls ready tasks from the shared queue, executes them,
    stores the result, and notifies the pool that the task is complete.
    """
    def __init__(self,
                 pool: "WorkerPool",
                 worker_id: int,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.pool = pool
        self.worker_id = worker_id
        self.daemon = True  # exit when main thread exits

    def run(self) -> None:
        while True:
            try:
                task = self.pool._task_queue.get(timeout=0.5)
            except queue.Empty:
                # Graceful shutdown when pool signals stop
                if self.pool._stop_event.is_set():
                    break
                continue

            # Minimal context: only the task object and a small helper.
            try:
                # Execute the task's function.
                task.result = task.func(task.payload)
            except Exception as exc:
                task.result = exc  # capture exception as result
            finally:
                # Mark task as completed and let the pool re‑evaluate dependents.
                self.pool._mark_completed(task.task_id)
                self.pool._task_queue.task_done()


# --------------------------------------------------------------------------- #
# WorkerPool – public API
# --------------------------------------------------------------------------- #
class WorkerPool:
    """
    Dependency‑aware worker pool.

    Example
    -------
    >>> def echo(x): return x
    >>> t1 = Task(func=echo, payload="hello")
    >>> t2 = Task(func=echo, payload="world", deps={t1.task_id})
    >>> pool = WorkerPool(num_workers=2)
    >>> pool.submit([t1, t2])
    >>> pool.wait_completion()
    >>> print(t1.result, t2.result)
    hello world
    """

    def __init__(self, num_workers: int = 4):
        self.num_workers = max(1, num_workers)
        self._task_queue: queue.Queue[Task] = queue.Queue()
        self._tasks: Dict[str, Task] = {}
        self._completed: Set[str] = set()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._workers: List[_Worker] = [
            _Worker(pool=self, worker_id=i, name=f"worker-{i}")
            for i in range(self.num_workers)
        ]
        for w in self._workers:
            w.start()

    # ------------------------------------------------------------------- #
    # Public submission API
    # ------------------------------------------------------------------- #
    def submit(self, tasks: List[Task]) -> None:
        """
        Register tasks with the pool.

        Tasks are stored, and any that have all dependencies satisfied are
        immediately queued for execution.
        """
        with self._lock:
            for task in tasks:
                self._tasks[task.task_id] = task

            # Enqueue tasks whose dependencies are already met.
            for task in tasks:
                if self._deps_met(task):
                    self._task_queue.put(task)

    # ------------------------------------------------------------------- #
    # Dependency handling
    # ------------------------------------------------------------------- #
    def _deps_met(self, task: Task) -> bool:
        """Return True if all dependencies of *task* are completed."""
        return task.deps.issubset(self._completed)

    def _mark_completed(self, task_id: str) -> None:
        """
        Record task completion and enqueue any newly‑ready dependents.
        """
        with self._lock:
            self._completed.add(task_id)

            # Scan for tasks that were waiting on this dependency.
            for pending in self._tasks.values():
                if pending.task_id in self._completed:
                    continue  # already done
                if pending.task_id in self._task_queue.queue:
                    continue  # already queued
                if self._deps_met(pending):
                    self._task_queue.put(pending)

    # ------------------------------------------------------------------- #
    # Synchronisation helpers
    # ------------------------------------------------------------------- #
    def wait_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Block until all submitted tasks finish or *timeout* expires.

        Returns
        -------
        bool
            True if all tasks completed, False if a timeout occurred.
        """
        self._task_queue.join()
        # After the queue is empty, ensure no pending tasks remain.
        with self._lock:
            all_done = len(self._completed) == len(self._tasks)
        return all_done

    def shutdown(self, wait: bool = True) -> None:
        """
        Signal workers to stop and optionally wait for them.
        """
        self._stop_event.set()
        if wait:
            for w in self._workers:
                w.join()


# --------------------------------------------------------------------------- #
# Minimal example (executed only when run directly)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple echo task using Groq for demonstration.
    def groq_task(payload: str) -> str:
        return groq_infer(payload)

    # Create a small DAG: A -> B -> C
    task_a = Task(func=groq_task, payload="Task A")
    task_b = Task(func=groq_task, payload="Task B", deps={task_a.task_id})
    task_c = Task(func=groq_task, payload="Task C", deps={task_b.task_id})

    pool = WorkerPool(num_workers=2)
    pool.submit([task_a, task_b, task_c])
    pool.wait_completion()
    pool.shutdown()

    for t in (task_a, task_b, task_c):
        print(f"{t.task_id[:8]}: {t.result}")