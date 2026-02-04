"""
atomizer.py

Implements the **Atomizer** – a lightweight dependency‑graph builder and
parallel task scheduler.

The core responsibilities:
* Accept a list of task specifications.
* Build a directed acyclic graph (DAG) based on explicit ``depends_on``
  relationships.
* Provide a ``schedule`` method that yields batches of tasks that can be
  executed in parallel (i.e., tasks with no unsatisfied dependencies).
* Execute tasks concurrently using ``concurrent.futures.ThreadPoolExecutor``
  while preserving dependency ordering.

The implementation is deliberately minimal yet fully typed and unit‑tested.
"""

from __future__ import annotations

import concurrent.futures
import itertools
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple


@dataclass(frozen=True)
class TaskSpec:
    """Immutable description of a single task."""
    task_id: str
    func: Callable[..., Any]
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    depends_on: Set[str] = field(default_factory=set)


class Atomizer:
    """
    Build a dependency graph from ``TaskSpec`` objects and schedule them for
    parallel execution while respecting dependencies.
    """

    def __init__(self, tasks: Iterable[TaskSpec]) -> None:
        self._tasks: Dict[str, TaskSpec] = {t.task_id: t for t in tasks}
        self._graph: Dict[str, Set[str]] = defaultdict(set)   # child -> parents
        self._reverse: Dict[str, Set[str]] = defaultdict(set) # parent -> children
        self._validate_and_build_graph()

    # --------------------------------------------------------------------- #
    # Graph construction & validation
    # --------------------------------------------------------------------- #
    def _validate_and_build_graph(self) -> None:
        # Ensure all referenced dependencies exist
        for task in self._tasks.values():
            for dep in task.depends_on:
                if dep not in self._tasks:
                    raise ValueError(f"Task '{task.task_id}' depends on unknown task '{dep}'")
                self._graph[task.task_id].add(dep)
                self._reverse[dep].add(task.task_id)

        # Detect cycles using Kahn's algorithm (raise if any remain)
        if self._has_cycle():
            raise ValueError("Dependency graph contains a cycle")

    def _has_cycle(self) -> bool:
        indegree = {tid: len(parents) for tid, parents in self._graph.items()}
        # Tasks without explicit entry in _graph have indegree 0
        for tid in self._tasks:
            indegree.setdefault(tid, 0)

        queue = deque([tid for tid, deg in indegree.items() if deg == 0])
        visited = 0

        while queue:
            node = queue.popleft()
            visited += 1
            for child in self._reverse.get(node, []):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        return visited != len(self._tasks)

    # --------------------------------------------------------------------- #
    # Scheduling API
    # --------------------------------------------------------------------- #
    def ready_batches(self) -> List[Set[str]]:
        """
        Return a list of batches. Each batch is a set of task IDs that can be
        executed concurrently. Batches are ordered such that all dependencies of
        a batch appear in earlier batches.
        """
        indegree = {tid: len(parents) for tid, parents in self._graph.items()}
        for tid in self._tasks:
            indegree.setdefault(tid, 0)

        batches: List[Set[str]] = []
        ready = {tid for tid, deg in indegree.items() if deg == 0}

        while ready:
            batches.append(set(ready))
            next_ready: Set[str] = set()
            for node in ready:
                for child in self._reverse.get(node, []):
                    indegree[child] -= 1
                    if indegree[child] == 0:
                        next_ready.add(child)
            ready = next_ready

        if sum(len(b) for b in batches) != len(self._tasks):
            raise RuntimeError("Failed to schedule all tasks – possible hidden cycle")
        return batches

    def schedule(
        self,
        max_workers: int = 4,
        timeout: float | None = None,
    ) -> Dict[str, Any]:
        """
        Execute all tasks respecting dependencies and return a mapping
        ``task_id -> result``.

        Parameters
        ----------
        max_workers: int
            Upper bound for the thread pool.
        timeout: float | None
            Optional overall timeout (seconds). ``None`` means no timeout.
        """
        results: Dict[str, Any] = {}
        batches = self.ready_batches()

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for batch in batches:
                futures = {
                    executor.submit(self._run_task, self._tasks[tid]): tid
                    for tid in batch
                }
                # Wait for the current batch to finish before moving on
                done, _ = concurrent.futures.wait(
                    futures.keys(),
                    timeout=timeout,
                    return_when=concurrent.futures.ALL_COMPLETED,
                )
                if not done:
                    raise TimeoutError("Batch execution exceeded timeout")
                for future in done:
                    tid = futures[future]
                    results[tid] = future.result()
        return results

    @staticmethod
    def _run_task(task: TaskSpec) -> Any:
        return task.func(*task.args, **task.kwargs)


# ------------------------------------------------------------------------- #
# Convenience factory for quick usage (not part of the class API)
# ------------------------------------------------------------------------- #
def atomize_and_execute(
    specs: Iterable[TaskSpec],
    max_workers: int = 4,
    timeout: float | None = None,
) -> Dict[str, Any]:
    """
    One‑liner helper: build an ``Atomizer`` from ``specs`` and run it.
    """
    return Atomizer(specs).schedule(max_workers=max_workers, timeout=timeout)