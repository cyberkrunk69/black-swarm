"""
task_scheduler.py

Implements a lightweight dependency‑aware task scheduler.

Features
--------
* DependencyGraph – stores tasks and their dependencies, validates DAG,
  provides topological ordering and simple textual visualisation.
* TaskScheduler – high‑level façade:
    - add_task(name, func, description)
    - auto‑detects dependencies from *description* using the pattern
      ``depends on <TASK_NAME>`` (case‑insensitive).
    - run() executes tasks in parallel where possible while respecting
      dependency constraints.
    - progress tracking via callbacks and a printable dependency graph.

The module is deliberately self‑contained (no external libraries) and can be
imported by ``grind_spawner.py`` (or any other component) without modifying
read‑only core files.
"""

from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from typing import Callable, Dict, List, Set, Tuple, Optional


class DependencyGraph:
    """
    Directed Acyclic Graph (DAG) representing task dependencies.

    Nodes are task names (str).  An edge ``A -> B`` means *B* depends on *A*
    (i.e., *A* must finish before *B* can start).
    """

    _DEP_PATTERN = re.compile(r"depends on (\w+)", re.IGNORECASE)

    def __init__(self) -> None:
        self._adj: Dict[str, Set[str]] = defaultdict(set)   # key -> set of successors
        self._rev_adj: Dict[str, Set[str]] = defaultdict(set)   # key -> set of predecessors
        self._tasks: Set[str] = set()

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def add_task(self, name: str, description: str = "") -> None:
        """Register a task and optionally infer its dependencies from *description*."""
        if name in self._tasks:
            raise ValueError(f"Task '{name}' already exists in the graph.")
        self._tasks.add(name)

        # Detect dependencies in description
        for dep in self._extract_deps(description):
            self.add_dependency(dep, name)

        # Ensure node exists in adjacency structures even if it has no edges
        self._adj.setdefault(name, set())
        self._rev_adj.setdefault(name, set())

    def add_dependency(self, predecessor: str, successor: str) -> None:
        """
        Declare that *successor* depends on *predecessor* (predecessor → successor).
        Both tasks must already be added via ``add_task``.
        """
        if predecessor not in self._tasks:
            raise ValueError(f"Predecessor task '{predecessor}' is undefined.")
        if successor not in self._tasks:
            raise ValueError(f"Successor task '{successor}' is undefined.")
        self._adj[predecessor].add(successor)
        self._rev_adj[successor].add(predecessor)

        if self._has_cycle():
            # rollback the edge before raising
            self._adj[predecessor].remove(successor)
            self._rev_adj[successor].remove(predecessor)
            raise ValueError(f"Adding dependency {predecessor} -> {successor} creates a cycle.")

    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """
        Return a list of tasks whose dependencies are all satisfied (i.e. all
        predecessors are in *completed*).  Tasks already in *completed* are excluded.
        """
        ready = [
            node
            for node in self._tasks
            if node not in completed and self._rev_adj[node].issubset(completed)
        ]
        return ready

    def topological_sort(self) -> List[str]:
        """Return a topological ordering of the tasks (raises if cycle detected)."""
        in_degree: Dict[str, int] = {node: len(preds) for node, preds in self._rev_adj.items()}
        zero_q = deque([n for n, deg in in_degree.items() if deg == 0])
        order: List[str] = []

        while zero_q:
            node = zero_q.popleft()
            order.append(node)
            for succ in self._adj[node]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    zero_q.append(succ)

        if len(order) != len(self._tasks):
            raise RuntimeError("Cycle detected in dependency graph during topological sort.")
        return order

    def visualize(self) -> str:
        """
        Simple textual representation of the graph.
        Example:
            A -> B, C
            B -> D
            C -> D
            D
        """
        lines = []
        for node in sorted(self._tasks):
            succs = sorted(self._adj.get(node, []))
            if succs:
                lines.append(f"{node} -> {', '.join(succs)}")
            else:
                lines.append(f"{node}")
        return "\n".join(lines)

    # --------------------------------------------------------------------- #
    # Internals
    # --------------------------------------------------------------------- #
    @staticmethod
    def _extract_deps(text: str) -> List[str]:
        """Parse ``depends on XYZ`` fragments from *text*."""
        return DependencyGraph._DEP_PATTERN.findall(text)

    def _has_cycle(self) -> bool:
        """Detect cycles using Kahn's algorithm – returns True if a cycle exists."""
        try:
            self.topological_sort()
            return False
        except RuntimeError:
            return True


class TaskScheduler:
    """
    High‑level scheduler that:
        * registers tasks (callables) together with a free‑form description,
        * auto‑detects dependencies,
        * runs tasks in parallel whenever their dependencies are satisfied,
        * provides progress callbacks and a printable dependency graph.
    """

    def __init__(self, max_workers: Optional[int] = None) -> None:
        self._graph = DependencyGraph()
        self._funcs: Dict[str, Callable[[], None]] = {}
        self._descriptions: Dict[str, str] = {}
        self._max_workers = max_workers
        self._lock = threading.Lock()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._progress_callback: Optional[Callable[[str, str], None]] = None  # (task, status)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def add_task(
        self,
        name: str,
        func: Callable[[], None],
        description: str = "",
    ) -> None:
        """
        Register a task.

        Parameters
        ----------
        name: Unique identifier for the task.
        func: Callable with no arguments that performs the work.
        description: Free‑form text.  Any phrase matching ``depends on <NAME>``
                     will be interpreted as a dependency.
        """
        if name in self._funcs:
            raise ValueError(f"Task '{name}' already registered.")
        self._funcs[name] = func
        self._descriptions[name] = description
        self._graph.add_task(name, description)

    def set_progress_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Register a callback to receive progress updates.

        The callback receives two arguments:
            * task name
            * status – one of ``'started'``, ``'finished'``, ``'failed'``
        """
        self._progress_callback = callback

    def run(self) -> None:
        """
        Execute all registered tasks respecting dependencies.
        Independent tasks are run in parallel using a thread pool.
        The method blocks until every task has either succeeded or failed.
        """
        if not self._funcs:
            return  # nothing to do

        # Validate that every dependency refers to a known task (graph already does this)
        # Use a thread pool; size defaults to min(32, os.cpu_count() + 4) if None
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Mapping of future -> task name
            futures: Dict[threading.Future, str] = {}

            while True:
                # Determine tasks ready to run that are not already submitted
                ready = self._graph.get_ready_tasks(self._completed.union(self._failed))
                for task_name in ready:
                    if task_name in futures.values():
                        continue  # already submitted

                    func = self._funcs[task_name]
                    future = executor.submit(self._run_wrapper, task_name, func)
                    futures[future] = task_name

                if not futures:
                    # No tasks left to submit and none running – we are done
                    break

                # Wait for any future to complete
                done, _ = as_completed(futures.keys(), timeout=None, return_when='FIRST_COMPLETED')
                for future in done:
                    task_name = futures.pop(future)
                    try:
                        future.result()  # re‑raise any exception
                        self._mark_completed(task_name)
                    except Exception as exc:
                        self._mark_failed(task_name, exc)

                # Loop again – new tasks may become ready after dependencies finish

    def visualize(self) -> str:
        """Return a textual representation of the current dependency graph."""
        return self._graph.visualize()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _run_wrapper(self, name: str, func: Callable[[], None]) -> None:
        """Execute *func* while emitting start/finish events."""
        self._emit_progress(name, "started")
        func()
        self._emit_progress(name, "finished")

    def _emit_progress(self, name: str, status: str) -> None:
        if self._progress_callback:
            try:
                self._progress_callback(name, status)
            except Exception:
                # Swallow errors from user‑provided callbacks – they must not break scheduling
                pass

    def _mark_completed(self, name: str) -> None:
        with self._lock:
            self._completed.add(name)

    def _mark_failed(self, name: str, exc: Exception) -> None:
        with self._lock:
            self._failed.add(name)
        self._emit_progress(name, "failed")
        # Optionally, log the exception – for this lightweight implementation we just
        # keep the failure set.  Users can inspect `self._failed` after `run()` returns.


# -------------------------------------------------------------------------
# Example usage (for documentation / quick manual testing)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    import time

    def mk_task(duration, result=None):
        def _inner():
            time.sleep(duration)
            if result is not None:
                print(f"Result: {result}")
        return _inner

    scheduler = TaskScheduler()
    scheduler.add_task("A", mk_task(1, "A done"))
    scheduler.add_task("B", mk_task(2, "B done"), description="depends on A")
    scheduler.add_task("C", mk_task(1, "C done"), description="depends on A")
    scheduler.add_task("D", mk_task(0.5, "D done"), description="depends on B, depends on C")

    print("Dependency graph:")
    print(scheduler.visualize())
    print("\nRunning tasks...\n")
    scheduler.run()
    print("\nAll done.")