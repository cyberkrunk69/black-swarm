"""
task_scheduler.py
-----------------

Implementation of a lightweight **Task Dependency Scheduler** as described in
`TASK_DEPENDENCY_DESIGN.md`.

Key Features
~~~~~~~~~~~~
* **DependencyGraph** – stores tasks, their textual definitions and inferred
  dependencies.  Provides cycle detection and topological sorting.
* **TaskScheduler** – consumes a DependencyGraph, automatically extracts
  dependencies from task text, and executes tasks in parallel whenever
  possible.
* **Auto‑detection** – looks for patterns such as ``DependsOn: task_a, task_b``
  (case‑insensitive) inside the free‑form task description.
* **Parallel Execution** – uses :class:`concurrent.futures.ThreadPoolExecutor`
  (IO‑bound tasks) with a configurable worker count.
* **Blocking on unmet dependencies** – a task is submitted only after all its
  declared dependencies have finished successfully.
* **Progress tracking & visualization** – simple console progress bar (via
  ``tqdm``) and an ASCII‑art dependency graph for quick inspection.

Integration
~~~~~~~~~~~
The module is imported by ``grind_spawner.py`` (read‑only) which expects a
``TaskScheduler`` class exposing a ``run_all()`` method.  No changes to
``grind_spawner.py`` are required – simply ``from .task_scheduler import
TaskScheduler``.

"""

import re
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Set, Tuple

from tqdm import tqdm


# --------------------------------------------------------------------------- #
# DependencyGraph
# --------------------------------------------------------------------------- #
class DependencyGraph:
    """
    Directed acyclic graph (DAG) representing tasks and their dependencies.

    Nodes are identified by a unique ``task_id`` (string).  Each node stores:
        * ``func`` – a callable that implements the task.
        * ``description`` – free‑form text (used for auto‑detecting deps).
        * ``deps`` – a set of ``task_id`` strings this task depends on.
    """

    _DEP_REGEX = re.compile(
        r"^\s*DependsOn\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE
    )

    def __init__(self) -> None:
        self._tasks: Dict[str, Callable[[], None]] = {}
        self._descriptions: Dict[str, str] = {}
        self._deps: Dict[str, Set[str]] = defaultdict(set)
        self._reverse_deps: Dict[str, Set[str]] = defaultdict(set)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def add_task(
        self,
        task_id: str,
        func: Callable[[], None],
        description: str = "",
    ) -> None:
        """
        Register a new task.

        Parameters
        ----------
        task_id: str
            Unique identifier.
        func: Callable[[], None]
            The callable that performs the work.
        description: str
            Optional free‑form description; used for dependency auto‑detection.
        """
        if task_id in self._tasks:
            raise ValueError(f"Task '{task_id}' already exists.")
        self._tasks[task_id] = func
        self._descriptions[task_id] = description
        # Auto‑detect dependencies from description
        auto_deps = self._parse_deps_from_text(description)
        for dep in auto_deps:
            self.add_dependency(task_id, dep)

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """
        Explicitly add a dependency edge ``depends_on -> task_id``.
        """
        if task_id == depends_on:
            raise ValueError("A task cannot depend on itself.")
        self._deps[task_id].add(depends_on)
        self._reverse_deps[depends_on].add(task_id)

    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """
        Return a list of task IDs whose dependencies are all satisfied
        (i.e. present in ``completed``) and that have not yet been executed.
        """
        ready = []
        for task_id in self._tasks:
            if task_id in completed:
                continue
            if self._deps[task_id].issubset(completed):
                ready.append(task_id)
        return ready

    def topological_sort(self) -> List[str]:
        """
        Return a topologically sorted list of task IDs.
        Raises ``ValueError`` if a cycle is detected.
        """
        in_degree: Dict[str, int] = {tid: 0 for tid in self._tasks}
        for deps in self._deps.values():
            for dep in deps:
                if dep not in in_degree:
                    raise ValueError(f"Dependency on unknown task '{dep}'.")
                in_degree[dep] += 1

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        sorted_list = []

        while queue:
            node = queue.popleft()
            sorted_list.append(node)
            for succ in self._reverse_deps.get(node, []):
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        if len(sorted_list) != len(self._tasks):
            raise ValueError("Cycle detected in task dependency graph.")
        return sorted_list

    def visualize(self) -> str:
        """
        Return a simple ASCII representation of the dependency graph.
        """
        lines = []
        for task_id in self._tasks:
            deps = ", ".join(sorted(self._deps[task_id])) or "None"
            lines.append(f"{task_id} <- [{deps}]")
        return "\n".join(lines)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    @classmethod
    def _parse_deps_from_text(cls, text: str) -> Set[str]:
        """
        Look for a line starting with ``DependsOn:`` and extract a comma‑separated
        list of task IDs.
        """
        matches = cls._DEP_REGEX.findall(text)
        deps: Set[str] = set()
        for match in matches:
            parts = [p.strip() for p in match.split(",")]
            deps.update(filter(None, parts))
        return deps

    # ------------------------------------------------------------------- #
    # Accessors used by the scheduler
    # ------------------------------------------------------------------- #
    @property
    def tasks(self) -> Dict[str, Callable[[], None]]:
        return self._tasks

    @property
    def dependencies(self) -> Dict[str, Set[str]]:
        return self._deps


# --------------------------------------------------------------------------- #
# TaskScheduler
# --------------------------------------------------------------------------- #
class TaskScheduler:
    """
    Orchestrates execution of tasks stored in a :class:`DependencyGraph`.

    Example
    -------
    >>> graph = DependencyGraph()
    >>> graph.add_task('download', lambda: print('download'), 'No deps')
    >>> graph.add_task('process', lambda: print('process'), 'DependsOn: download')
    >>> scheduler = TaskScheduler(graph, max_workers=4)
    >>> scheduler.run_all()
    """

    def __init__(
        self,
        graph: DependencyGraph,
        max_workers: int = 4,
        progress_desc: str = "Running tasks",
    ) -> None:
        self.graph = graph
        self.max_workers = max_workers
        self.progress_desc = progress_desc
        self._lock = threading.Lock()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()

    def run_all(self) -> Tuple[Set[str], Set[str]]:
        """
        Execute all tasks respecting dependencies.

        Returns
        -------
        completed: set of task IDs that finished successfully.
        failed: set of task IDs that raised an exception.
        """
        total_tasks = len(self.graph.tasks)
        if total_tasks == 0:
            print("[TaskScheduler] No tasks to run.")
            return set(), set()

        print("[TaskScheduler] Dependency graph:")
        print(self.graph.visualize())
        print("-" * 40)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Mapping of Future -> task_id
            futures: Dict[threading.Future, str] = {}

            pbar = tqdm(total=total_tasks, desc=self.progress_desc, unit="task")

            while len(self._completed) + len(self._failed) < total_tasks:
                # Determine which tasks are ready and not yet submitted
                ready = self.graph.get_ready_tasks(self._completed)
                for task_id in ready:
                    if task_id in futures.values():
                        continue  # already submitted
                    func = self.graph.tasks[task_id]
                    future = executor.submit(self._run_task_wrapper, task_id, func)
                    futures[future] = task_id

                # Wait for any future to complete
                if not futures:
                    # No runnable tasks – must be a deadlock (cycle or missing dep)
                    raise RuntimeError(
                        "Deadlock detected: no runnable tasks but work remains."
                    )
                done, _ = as_completed(futures, timeout=0.1), None
                for future in done:
                    task_id = futures.pop(future)
                    try:
                        future.result()  # re‑raise any exception
                        with self._lock:
                            self._completed.add(task_id)
                    except Exception as exc:
                        print(f"[TaskScheduler] Task '{task_id}' failed: {exc}")
                        with self._lock:
                            self._failed.add(task_id)
                    finally:
                        pbar.update(1)

            pbar.close()

        print("[TaskScheduler] Execution finished.")
        print(f"  Completed: {len(self._completed)}")
        print(f"  Failed   : {len(self._failed)}")
        return self._completed, self._failed

    # ------------------------------------------------------------------- #
    # Helper
    # ------------------------------------------------------------------- #
    @staticmethod
    def _run_task_wrapper(task_id: str, func: Callable[[], None]) -> None:
        """
        Simple wrapper that prints start/finish messages and executes the task.
        """
        print(f"[TaskScheduler] START  : {task_id}")
        func()
        print(f"[TaskScheduler] FINISH : {task_id}")


# --------------------------------------------------------------------------- #
# Convenience function for external callers (e.g., grind_spawner.py)
# --------------------------------------------------------------------------- #
def build_scheduler_from_definitions(
    definitions: List[Tuple[str, Callable[[], None], str]],
    max_workers: int = 4,
) -> TaskScheduler:
    """
    Helper to create a ``TaskScheduler`` from a list of task definitions.

    Parameters
    ----------
    definitions: List[Tuple[task_id, callable, description]]
        Each tuple defines a task.
    max_workers: int
        Number of parallel workers.

    Returns
    -------
    TaskScheduler instance ready to ``run_all()``.
    """
    graph = DependencyGraph()
    for task_id, func, description in definitions:
        graph.add_task(task_id, func, description)
    return TaskScheduler(graph, max_workers=max_workers)


# --------------------------------------------------------------------------- #
# If this module is executed directly, run a tiny demo.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Demo tasks
    import time

    def t1():
        time.sleep(1)
        print(">>> t1 done")

    def t2():
        time.sleep(2)
        print(">>> t2 done")

    def t3():
        time.sleep(0.5)
        print(">>> t3 done")

    demo_defs = [
        ("download_data", t1, "No deps"),
        ("process_data", t2, "DependsOn: download_data"),
        ("export_results", t3, "DependsOn: process_data"),
    ]

    scheduler = build_scheduler_from_definitions(demo_defs, max_workers=3)
    scheduler.run_all()