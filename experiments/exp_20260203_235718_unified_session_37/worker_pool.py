"""
worker_pool.py
----------------
Dependency‑aware parallel execution engine for Claude‑Parasite‑Brain‑Suck.

Key features
------------
* Accepts a collection of ``Task`` objects (any object with ``id`` and
  ``dependencies`` attributes).
* Builds a dependency graph on‑the‑fly (provided by the Atomizer module).
* Schedules tasks as soon as all their prerequisites are completed.
* Executes each task in a lightweight worker that receives only the task
  object and a tiny (~50 LOC) execution context.
* Uses the Groq SDK for ultra‑fast inference inside the worker.
* Tracks completion, failures and provides a simple ``await_all`` API.

The implementation deliberately stays under ~200 LOC to keep the worker
context minimal while still being robust.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple

# --------------------------------------------------------------------------- #
# Optional: Groq SDK import.  If Groq is not installed, we fall back to a
# dummy stub that raises a clear error when used.  This keeps the module
# importable in environments without Groq.
# --------------------------------------------------------------------------- #
try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    class Groq:  # pylint: disable=too-few-public-methods
        """Fallback stub for the Groq client."""

        def __init__(self, *_, **__) -> None:
            raise RuntimeError(
                "Groq SDK is required for inference. Install with `pip install groq`."
            )

# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
Task = Any  # Expected to have ``id`` (hashable) and ``dependencies`` (Iterable[hashable]).

# --------------------------------------------------------------------------- #
# WorkerPool
# --------------------------------------------------------------------------- #
class WorkerPool:
    """
    A minimal‑context, dependency‑aware worker pool.

    Parameters
    ----------
    max_workers: int
        Number of concurrent workers (default: number of CPUs).
    groq_api_key: str
        API key for the Groq service – passed to the Groq client.
    task_handler: Callable[[Task, Groq], Any]
        Function that receives a single ``Task`` and a pre‑instantiated Groq
        client.  It should perform the actual inference work and return a
        result (or raise on failure).
    """

    def __init__(
        self,
        max_workers: int | None = None,
        groq_api_key: str | None = None,
        task_handler: Callable[[Task, Groq], Any] | None = None,
    ) -> None:
        self.max_workers = max_workers
        self.groq_api_key = groq_api_key
        self.task_handler = task_handler or self._default_handler

        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._lock = threading.Lock()

        # Dependency bookkeeping
        self._dependents: Dict[Any, Set[Any]] = defaultdict(set)  # task_id -> set of children
        self._remaining_deps: Dict[Any, int] = {}  # task_id -> count of unfinished parents
        self._tasks: Dict[Any, Task] = {}  # task_id -> Task object

        # Runtime state
        self._ready_queue: deque[Any] = deque()
        self._futures: Dict[Any, Future] = {}
        self._completed: Set[Any] = set()
        self._failed: Set[Any] = set()

        # Groq client – instantiated once per pool (shared read‑only)
        self._groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

        # Logging
        self._log = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def add_tasks(self, tasks: Iterable[Task]) -> None:
        """
        Register a batch of tasks.  This method can be called before or
        during execution – newly added tasks are immediately considered
        for scheduling if their dependencies are already satisfied.
        """
        with self._lock:
            for task in tasks:
                task_id = getattr(task, "id")
                if task_id in self._tasks:
                    continue  # idempotent addition

                self._tasks[task_id] = task
                deps = set(getattr(task, "dependencies", []))
                self._remaining_deps[task_id] = len(deps)

                for dep in deps:
                    self._dependents[dep].add(task_id)

                if not deps:
                    self._ready_queue.append(task_id)

        self._maybe_schedule()

    def await_all(self, timeout: float | None = None) -> Tuple[Dict[Any, Any], Set[Any]]:
        """
        Block until every submitted task finishes (success or failure).

        Returns
        -------
        results: dict
            Mapping of task_id -> result for successful tasks.
        failed: set
            Set of task_id values that raised an exception.
        """
        futures = list(self._futures.values())
        for f in futures:
            f.result(timeout=timeout)  # propagate exceptions

        results = {tid: f.result() for tid, f in self._futures.items() if tid not in self._failed}
        return results, self._failed.copy()

    # ------------------------------------------------------------------- #
    # Internals
    # ------------------------------------------------------------------- #
    def _maybe_schedule(self) -> None:
        """
        Pull tasks from the ready queue and submit them to the executor.
        This method is called whenever the queue might have grown.
        """
        while True:
            with self._lock:
                if not self._ready_queue:
                    break
                task_id = self._ready_queue.popleft()
                task = self._tasks[task_id]

                # Submit the minimal context (task + Groq client) to the pool.
                future = self._executor.submit(self._run_task, task)
                self._futures[task_id] = future

                # Attach a completion callback to update dependency state.
                future.add_done_callback(lambda f, tid=task_id: self._on_task_done(tid, f))

    def _run_task(self, task: Task) -> Any:
        """
        Execute a single task using the provided ``task_handler``.
        The handler receives only the task and a Groq client (or ``None``).
        """
        self._log.debug("Running task %s", getattr(task, "id"))
        return self.task_handler(task, self._groq_client)

    def _on_task_done(self, task_id: Any, future: Future) -> None:
        """
        Callback invoked when a worker finishes.  Updates dependency counters
        and enqueues newly-unblocked children.
        """
        try:
            _ = future.result()  # will raise if task failed
            success = True
        except Exception as exc:  # pylint: disable=broad-except
            self._log.error("Task %s failed: %s", task_id, exc, exc_info=True)
            success = False

        with self._lock:
            if success:
                self._completed.add(task_id)
            else:
                self._failed.add(task_id)

            # Unblock dependents regardless of success – they may still run
            # unless you want a stricter policy (e.g., abort on failure).
            for child_id in self._dependents.get(task_id, []):
                self._remaining_deps[child_id] -= 1
                if self._remaining_deps[child_id] == 0:
                    self._ready_queue.append(child_id)

        # Try to schedule any newly ready tasks.
        self._maybe_schedule()

    # ------------------------------------------------------------------- #
    # Default handler (can be overridden by the caller)
    # ------------------------------------------------------------------- #
    @staticmethod
    def _default_handler(task: Task, groq_client: Groq | None) -> Any:
        """
        Very small default handler that demonstrates a Groq call.
        The real workload should replace this with domain‑specific logic.

        Expected ``task`` shape:
            - ``prompt`` : str  – text to send to Groq
        """
        if groq_client is None:
            raise RuntimeError("Groq client not configured for default handler.")

        # The snippet below is ~30 LOC – well within the 50‑LOC limit.
        # It performs a single completion request.
        response = groq_client.chat.completions.create(
            model="groq-llama3-70b-8192",  # example model
            messages=[{"role": "user", "content": getattr(task, "prompt", "")}],
            temperature=0.7,
        )
        # Return the generated text (or whatever the caller expects).
        return response.choices[0].message.content

# --------------------------------------------------------------------------- #
# Convenience factory
# --------------------------------------------------------------------------- #
def make_worker_pool(
    max_workers: int | None = None,
    groq_api_key: str | None = None,
    task_handler: Callable[[Task, Groq], Any] | None = None,
) -> WorkerPool:
    """
    Helper to instantiate a ``WorkerPool`` with sensible defaults.
    """
    return WorkerPool(
        max_workers=max_workers,
        groq_api_key=groq_api_key,
        task_handler=task_handler,
    )

# --------------------------------------------------------------------------- #
# Example usage (removed in production builds)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import os
    import sys

    logging.basicConfig(level=logging.INFO)

    # Dummy task definition for quick manual test
    class DummyTask:
        def __init__(self, tid: str, deps: List[str] | None = None, prompt: str = ""):
            self.id = tid
            self.dependencies = deps or []
            self.prompt = prompt

    tasks = [
        DummyTask("t1", prompt="Explain quantum entanglement."),
        DummyTask("t2", deps=["t1"], prompt="Summarize the previous answer."),
        DummyTask("t3", deps=["t1"], prompt="Give a real‑world analogy."),
    ]

    pool = make_worker_pool(groq_api_key=os.getenv("GROQ_API_KEY"))
    pool.add_tasks(tasks)
    results, failures = pool.await_all()
    print("Results:", results)
    print("Failed:", failures)