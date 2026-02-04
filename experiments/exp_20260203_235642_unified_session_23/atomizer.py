"""
Atomizer – Core component for dependency graph construction and parallel task scheduling.

Features
--------
* Register tasks with explicit dependencies.
* Perform topological sort to produce a valid execution order.
* Execute tasks in parallel while respecting dependency constraints using
  ``concurrent.futures.ThreadPoolExecutor``.
* Simple, dependency‑free implementation (uses only the Python stdlib).

Usage
-----
>>> from atomizer import Atomizer
>>> a = Atomizer(max_workers=4)
>>> a.add_task('task_a', [], lambda: 'A')
>>> a.add_task('task_b', ['task_a'], lambda: 'B')
>>> results = a.run()
>>> results['task_b']   # => 'B'
"""

from __future__ import annotations

from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple


class Atomizer:
    """
    Manages a directed acyclic graph (DAG) of tasks and runs them in parallel
    while respecting dependencies.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._graph: Dict[str, Set[str]] = defaultdict(set)   # node -> set of dependent nodes
        self._reverse: Dict[str, Set[str]] = defaultdict(set)  # node -> set of prerequisites
        self._tasks: Dict[str, Callable[[], Any]] = {}

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def add_task(self, name: str, dependencies: Iterable[str], fn: Callable[[], Any]) -> None:
        """
        Register a new task.

        Parameters
        ----------
        name: str
            Unique identifier for the task.
        dependencies: Iterable[str]
            Names of tasks that must complete before *name* can run.
        fn: Callable[[], Any]
            Zero‑argument function that performs the work and returns a result.
        """
        if name in self._tasks:
            raise ValueError(f"Task '{name}' already exists.")
        self._tasks[name] = fn
        for dep in dependencies:
            self._graph[dep].add(name)
            self._reverse[name].add(dep)

        # Ensure nodes exist even if they have no edges
        self._graph.setdefault(name, set())
        self._reverse.setdefault(name, set())

    def run(self) -> Dict[str, Any]:
        """
        Execute all registered tasks respecting dependencies.

        Returns
        -------
        dict
            Mapping from task name to the value returned by its callable.
        """
        order = self._topological_sort()
        results: Dict[str, Any] = {}
        in_progress: Set[str] = set()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Map of future -> task name
            future_to_task: Dict[Any, str] = {}

            # Helper to submit ready tasks
            def submit_ready():
                for task in order:
                    if task in results or task in in_progress:
                        continue
                    if self._reverse[task].issubset(results.keys()):
                        future = executor.submit(self._tasks[task])
                        future_to_task[future] = task
                        in_progress.add(task)

            submit_ready()
            while future_to_task:
                for future in as_completed(future_to_task):
                    task_name = future_to_task.pop(future)
                    in_progress.remove(task_name)
                    results[task_name] = future.result()
                submit_ready()

        return results

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _topological_sort(self) -> List[str]:
        """
        Perform Kahn's algorithm to produce a deterministic topological order.
        Raises RuntimeError if a cycle is detected.
        """
        indegree: Dict[str, int] = {node: len(self._reverse[node]) for node in self._graph}
        zero_indeg = deque([n for n, deg in indegree.items() if deg == 0])
        order: List[str] = []

        while zero_indeg:
            node = zero_indeg.popleft()
            order.append(node)
            for succ in self._graph[node]:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    zero_indeg.append(succ)

        if len(order) != len(self._graph):
            raise RuntimeError("Dependency graph contains a cycle.")
        return order