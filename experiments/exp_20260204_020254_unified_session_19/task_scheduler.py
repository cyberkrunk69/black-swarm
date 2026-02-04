"""
task_scheduler.py

Implements a lightweight dependency‑aware task scheduler used by the
grind_spawner workflow.

Key components
--------------
* **DependencyGraph** – builds a directed acyclic graph (DAG) from a list of
  task descriptors.  It can auto‑detect simple textual dependencies
  (e.g. “Task B depends on Task A”) and provides utilities for topological
  ordering, cycle detection and visualisation.

* **TaskScheduler** – consumes a ``DependencyGraph`` and executes the
  tasks.  Independent tasks are run in parallel using ``ThreadPoolExecutor``.
  Tasks block until all of their declared dependencies have completed.
  Progress is reported on the console and a simple ASCII‑art dependency
  visualisation is printed before execution starts.

The module is deliberately self‑contained – it only relies on the Python
standard library (``re``, ``concurrent.futures``, ``collections`` and
``textwrap``).  This keeps the integration with ``grind_spawner.py`` simple:
the spawner can import ``TaskScheduler`` and call ``schedule(tasks)`` where
``tasks`` is an iterable of ``Task`` objects (or any mapping with the required
attributes).

Typical usage from ``grind_spawner.py``::

    from task_scheduler import TaskScheduler, Task

    tasks = [
        Task(name="A", func=do_a, description="Initial step"),
        Task(name="B", func=do_b, description="Task B depends on Task A"),
        Task(name="C", func=do_c, description="Task C depends on Task A"),
        Task(name="D", func=do_d, description="Task D depends on Task B and Task C"),
    ]

    scheduler = TaskScheduler(tasks)
    results = scheduler.run()

The scheduler will automatically detect the dependencies expressed in the
``description`` field, build the DAG, visualise it, and then execute the tasks
concurrently where possible while respecting the dependency constraints.

"""

import re
import sys
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Set, Tuple, Any
import textwrap


# --------------------------------------------------------------------------- #
# Helper data structure representing a single unit of work
# --------------------------------------------------------------------------- #
@dataclass
class Task:
    """
    Simple container for a unit of work.

    Attributes
    ----------
    name: str
        Unique identifier for the task.
    func: Callable[[], Any]
        Callable that performs the work.  It receives no arguments and should
        return a result (or raise an exception on failure).
    description: str, optional
        Human‑readable description.  The scheduler scans this text for phrases
        like ``depends on <TaskName>`` to auto‑detect dependencies.
    """
    name: str
    func: Callable[[], Any]
    description: str = ""

    # Runtime fields (populated by the scheduler)
    result: Any = field(default=None, init=False)
    exception: Exception = field(default=None, init=False)


# --------------------------------------------------------------------------- #
# Dependency graph implementation
# --------------------------------------------------------------------------- #
class DependencyGraph:
    """
    Directed acyclic graph (DAG) representing task dependencies.

    The graph is built from a collection of :class:`Task` objects.
    Dependencies are inferred automatically from the ``description`` attribute
    using a simple regular expression pattern:

        r\"depends? on ([\\w-]+)\"   (case‑insensitive)

    The pattern extracts one or more task names.  Multiple dependencies can be
    expressed in a single description, e.g. ``Task D depends on Task B and Task C``.

    Public API
    ----------
    * ``add_task(task)`` – add a task (and its inferred edges) to the graph.
    * ``topological_sort()`` – returns a list of task names in a valid execution order.
    * ``get_ready_tasks(completed)`` – given a set of completed task names,
      returns the subset of tasks whose dependencies are satisfied.
    * ``visualize()`` – returns a multi‑line string visualising the DAG.
    """

    _DEP_REGEX = re.compile(r"depends?\s+on\s+([A-Za-z0-9_-]+)", re.IGNORECASE)

    def __init__(self) -> None:
        # adjacency list: key -> set of successors (tasks that depend on *key*)
        self._adj: Dict[str, Set[str]] = defaultdict(set)
        # reverse adjacency: key -> set of predecessors (tasks that *key* depends on)
        self._rev_adj: Dict[str, Set[str]] = defaultdict(set)
        # store the actual Task objects for later execution
        self._tasks: Dict[str, Task] = {}

    # ------------------------------------------------------------------- #
    # Public mutation helpers
    # ------------------------------------------------------------------- #
    def add_task(self, task: Task) -> None:
        if task.name in self._tasks:
            raise ValueError(f"Duplicate task name detected: {task.name}")

        self._tasks[task.name] = task
        deps = self._extract_dependencies(task.description)

        for dep in deps:
            if dep == task.name:
                raise ValueError(f"Task '{task.name}' cannot depend on itself.")
            self._adj[dep].add(task.name)          # edge dep -> task
            self._rev_adj[task.name].add(dep)      # edge task -> dep

        # Ensure nodes exist even if they have no edges
        self._adj.setdefault(task.name, set())
        self._rev_adj.setdefault(task.name, set())

    # ------------------------------------------------------------------- #
    # Dependency extraction
    # ------------------------------------------------------------------- #
    @classmethod
    def _extract_dependencies(cls, description: str) -> Set[str]:
        """
        Scan *description* for ``depends on <TaskName>`` patterns.

        Returns a set of task names (strings).  The search is case‑insensitive.
        """
        if not description:
            return set()
        matches = cls._DEP_REGEX.findall(description)
        # The regex only captures the first word after “depends on”.  To support
        # constructs like “depends on A and B”, we split on common conjunctions.
        deps: Set[str] = set()
        for match in matches:
            # Remove punctuation and split on common delimiters
            cleaned = re.sub(r"[.,;]", "", match)
            parts = re.split(r"\s+and\s+|\s+or\s+|\s*,\s*", cleaned, flags=re.IGNORECASE)
            deps.update(p.strip() for p in parts if p.strip())
        return deps

    # ------------------------------------------------------------------- #
    # Validation & ordering
    # ------------------------------------------------------------------- #
    def _detect_cycle(self) -> bool:
        """
        Detect cycles using Kahn's algorithm. Returns True if a cycle exists.
        """
        indegree = {node: len(preds) for node, preds in self._rev_adj.items()}
        queue = deque([n for n, d in indegree.items() if d == 0])
        visited = 0

        while queue:
            node = queue.popleft()
            visited += 1
            for succ in self._adj[node]:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    queue.append(succ)

        return visited != len(self._tasks)

    def topological_sort(self) -> List[str]:
        """
        Return a list of task names in a valid execution order.
        Raises ``ValueError`` if the graph contains a cycle.
        """
        if self._detect_cycle():
            raise ValueError("Dependency graph contains a cycle; cannot schedule tasks.")

        indegree = {node: len(preds) for node, preds in self._rev_adj.items()}
        queue = deque([n for n, d in indegree.items() if d == 0])
        order: List[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for succ in self._adj[node]:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    queue.append(succ)

        return order

    # ------------------------------------------------------------------- #
    # Runtime helpers
    # ------------------------------------------------------------------- #
    def get_ready_tasks(self, completed: Set[str]) -> List[Task]:
        """
        Return a list of tasks whose dependencies are all satisfied (i.e.
        all predecessors are in *completed*).  Tasks already completed are
        excluded.
        """
        ready: List[Task] = []
        for name, task in self._tasks.items():
            if name in completed:
                continue
            deps = self._rev_adj[name]
            if deps.issubset(completed):
                ready.append(task)
        return ready

    def get_task(self, name: str) -> Task:
        return self._tasks[name]

    # ------------------------------------------------------------------- #
    # Visualisation
    # ------------------------------------------------------------------- #
    def visualize(self) -> str:
        """
        Produce a simple ASCII representation of the DAG.

        Example output:

            A
            ├─> B
            └─> C
                └─> D
        """
        lines: List[str] = []
        # Build a reverse map: node -> list of children (already in _adj)
        # We'll start from roots (nodes with no incoming edges)
        roots = [n for n, preds in self._rev_adj.items() if not preds]
        visited: Set[str] = set()

        def _dfs(node: str, prefix: str = "") -> None:
            if node in visited:
                return
            visited.add(node)
            lines.append(f"{prefix}{node}")
            children = sorted(self._adj[node])
            for i, child in enumerate(children):
                connector = "├─> " if i < len(children) - 1 else "└─> "
                _dfs(child, prefix + connector)

        for root in sorted(roots):
            _dfs(root)

        if not lines:
            return "(empty graph)"
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Scheduler implementation
# --------------------------------------------------------------------------- #
class TaskScheduler:
    """
    Executes a collection of :class:`Task` objects respecting their
    dependencies.

    Features
    --------
    * Automatic detection of textual dependencies.
    * Parallel execution of tasks whose dependencies are satisfied.
    * Blocking semantics – a task does not start until all of its predecessors
      have finished successfully.
    * Simple console‑based progress reporting.
    * Optional ``max_workers`` to limit concurrency (defaults to number of CPUs).
    """

    def __init__(self,
                 tasks: Iterable[Task],
                 max_workers: int = None,
                 progress_interval: float = 0.5):
        """
        Parameters
        ----------
        tasks: iterable of Task
            The tasks to schedule.
        max_workers: int, optional
            Upper bound for concurrent threads.  ``None`` lets ``ThreadPoolExecutor``
            decide (defaults to ``os.cpu_count()``).
        progress_interval: float
            Seconds between progress prints.  Set to ``0`` to suppress periodic
            updates (final status will still be printed).
        """
        self.graph = DependencyGraph()
        for task in tasks:
            self.graph.add_task(task)

        self.max_workers = max_workers
        self.progress_interval = progress_interval

        # Runtime bookkeeping
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    def _run_task(self, task: Task) -> None:
        """
        Wrapper executed inside a worker thread.  Captures result / exception
        and updates shared state.
        """
        try:
            task.result = task.func()
        except Exception as exc:  # pylint: disable=broad-except
            task.exception = exc
            with self._lock:
                self._failed.add(task.name)
        finally:
            with self._lock:
                self._completed.add(task.name)
                self._condition.notify_all()

    def _schedule_ready_tasks(self,
                              executor: ThreadPoolExecutor,
                              pending_futures: Dict[threading.Thread, str]) -> None:
        """
        Submit all currently ready tasks to *executor*.
        ``pending_futures`` maps ``Future`` objects to the task name for bookkeeping.
        """
        ready_tasks = self.graph.get_ready_tasks(self._completed)
        for task in ready_tasks:
            if task.name in pending_futures.values():
                continue  # already submitted
            future = executor.submit(self._run_task, task)
            pending_futures[future] = task.name

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def run(self) -> Dict[str, Any]:
        """
        Execute the task graph.

        Returns
        -------
        dict
            Mapping from task name to its result (or ``None`` if the task raised
            an exception).  The caller can inspect ``Task.exception`` for error
            details.

        Raises
        ------
        RuntimeError
            If any task fails.  All tasks that could be scheduled before the
            failure are still completed.
        """
        print("\n=== Dependency Graph ===")
        print(self.graph.visualize())
        print("\n=== Scheduling ===\n")

        pending_futures: Dict[threading.Thread, str] = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Initial submission of tasks that have no dependencies
            self._schedule_ready_tasks(executor, pending_futures)

            while True:
                if not pending_futures:
                    # No tasks in flight – either we are done or dead‑locked
                    if len(self._completed) == len(self.graph._tasks):
                        break  # all done
                    # Dead‑lock detection (should not happen if graph is a DAG)
                    raise RuntimeError("Deadlock detected: no runnable tasks but graph not complete.")

                # Wait for any future to finish
                done, _ = as_completed(pending_futures.keys(), timeout=self.progress_interval), None

                # Process completed futures
                for future in list(pending_futures):
                    if future.done():
                        task_name = pending_futures.pop(future)
                        # Result already stored in the Task object; we just continue
                        # to possibly schedule new ready tasks.
                # After handling completions, attempt to schedule newly ready tasks
                self._schedule_ready_tasks(executor, pending_futures)

        # Final progress report
        print("\n=== Execution Summary ===")
        for name, task in self.graph._tasks.items():
            status = "FAILED" if task.exception else "OK"
            print(f"{name:20s} : {status}")

        if self._failed:
            failed_list = ", ".join(sorted(self._failed))
            raise RuntimeError(f"The following tasks failed: {failed_list}")

        # Return a dict of results
        return {name: task.result for name, task in self.graph._tasks.items()}


# --------------------------------------------------------------------------- #
# Convenience function for grind_spawner integration
# --------------------------------------------------------------------------- #
def schedule(tasks: Iterable[Task],
             max_workers: int = None) -> Dict[str, Any]:
    """
    Helper that creates a ``TaskScheduler`` and runs it.  This is the entry
    point expected by ``grind_spawner.py``.

    Parameters
    ----------
    tasks : iterable of Task
        Collection of tasks to execute.
    max_workers : int, optional
        Concurrency limit.

    Returns
    -------
    dict
        Mapping of task names to their results.
    """
    scheduler = TaskScheduler(tasks, max_workers=max_workers)
    return scheduler.run()