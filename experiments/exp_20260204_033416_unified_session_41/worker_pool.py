"""
worker_pool.py
----------------
A lightweight, dependency‑aware worker pool for executing Atomizer tasks in parallel.
Each worker receives only the minimal context required to run a single task
(~50 lines of code) and a Groq client for fast inference.

Key Features
------------
* Builds a ready‑queue from the dependency graph supplied by the Atomizer.
* Tracks task completion and releases dependent tasks as soon as all their
  prerequisites are satisfied.
* Uses a thread pool (configurable size) – threads are cheap because the heavy
  lifting (model inference) is off‑loaded to Groq.
* Minimal per‑worker payload – only the `Task` instance and a shared Groq client.
"""

from __future__ import annotations

import threading
from queue import Queue
from typing import Callable, Dict, Iterable, List, Set

# --------------------------------------------------------------------------- #
# External dependencies (assumed to be available in the environment)
# --------------------------------------------------------------------------- #
try:
    from groq import GroqClient  # Placeholder import – replace with actual Groq SDK
except Exception:  # pragma: no cover
    # Fallback stub for environments without Groq installed.
    class GroqClient:  # pylint: disable=too-few-public-methods
        def __init__(self, *_, **__): ...

# --------------------------------------------------------------------------- #
# Core data structures
# --------------------------------------------------------------------------- #
class Task:
    """
    Minimal representation of a unit of work produced by the Atomizer.
    The Atomizer must expose a ``run(groq_client)`` method that returns the
    task's result (or raises).  Only this method is used by the worker pool.
    """
    def __init__(self, name: str, run_fn: Callable[[GroqClient], object]):
        self.name = name
        self._run_fn = run_fn

    def run(self, client: GroqClient):
        """Execute the task using the provided Groq client."""
        return self._run_fn(client)

    def __repr__(self) -> str:
        return f"<Task {self.name}>"

# --------------------------------------------------------------------------- #
# WorkerPool implementation
# --------------------------------------------------------------------------- #
class WorkerPool:
    """
    Dependency‑aware pool that executes ``Task`` objects in parallel.

    Parameters
    ----------
    tasks : Dict[str, Task]
        Mapping from task identifier to ``Task`` instance.
    dependencies : Dict[str, Iterable[str]]
        Directed acyclic graph: ``dependencies[t]`` is the set of task IDs that
        must finish before ``t`` can start.
    max_workers : int, optional
        Number of concurrent worker threads (defaults to number of CPUs).
    groq_client_factory : Callable[[], GroqClient], optional
        Factory that creates a Groq client.  A single shared client is used by
        all workers to keep resource usage low.
    """
    def __init__(
        self,
        tasks: Dict[str, Task],
        dependencies: Dict[str, Iterable[str]],
        max_workers: int | None = None,
        groq_client_factory: Callable[[], GroqClient] | None = None,
    ):
        self._tasks = tasks
        self._deps = {k: set(v) for k, v in dependencies.items()}
        self._dependents: Dict[str, Set[str]] = {}
        for t, prereqs in self._deps.items():
            for p in prereqs:
                self._dependents.setdefault(p, set()).add(t)

        self._ready_queue: Queue[str] = Queue()
        self._completed: Set[str] = set()
        self._lock = threading.Lock()
        self._max_workers = max_workers or (threading.cpu_count() or 4)

        # Groq client – shared among workers (lightweight handle)
        self._client = (groq_client_factory or GroqClient)()

        # Populate initial ready tasks (no dependencies)
        for tid, prereqs in self._deps.items():
            if not prereqs:
                self._ready_queue.put(tid)
        # Also include tasks that are completely missing from the graph
        for tid in set(tasks) - set(self._deps):
            self._ready_queue.put(tid)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self) -> Dict[str, object]:
        """
        Execute all tasks respecting dependencies.

        Returns
        -------
        Dict[str, object]
            Mapping from task ID to its result.
        """
        results: Dict[str, object] = {}
        threads: List[threading.Thread] = []

        def worker() -> None:
            while True:
                try:
                    tid = self._ready_queue.get_nowait()
                except Exception:
                    # Queue empty – check if work is still pending
                    with self._lock:
                        if len(self._completed) == len(self._tasks):
                            break
                    continue

                task = self._tasks[tid]
                try:
                    result = task.run(self._client)  # Minimal context
                    results[tid] = result
                except Exception as exc:  # pragma: no cover
                    results[tid] = exc  # Store exception for caller inspection

                self._mark_completed(tid)

                self._ready_queue.task_done()

        # Spawn workers
        for _ in range(self._max_workers):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)

        # Wait for all work to finish
        for t in threads:
            t.join()

        return results

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _mark_completed(self, tid: str) -> None:
        """Mark ``tid`` as finished and release any dependents whose prereqs are met."""
        with self._lock:
            self._completed.add(tid)
            for dependent in self._dependents.get(tid, set()):
                remaining = self._deps[dependent] - self._completed
                if not remaining:
                    self._ready_queue.put(dependent)

# --------------------------------------------------------------------------- #
# Example usage (executed only when run as a script)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Mock tasks for demonstration – replace with real Atomizer output.
    def mk_task(i: int) -> Task:
        return Task(
            name=f"task_{i}",
            run_fn=lambda client: f"result_{i} (via {type(client).__name__})",
        )

    # Build a tiny DAG: 0 -> 2, 1 -> 2
    task_objs = {str(i): mk_task(i) for i in range(3)}
    deps = {"2": ["0", "1"]}  # task 2 depends on 0 and 1

    pool = WorkerPool(tasks=task_objs, dependencies=deps, max_workers=2)
    out = pool.run()
    print("Task results:", out)