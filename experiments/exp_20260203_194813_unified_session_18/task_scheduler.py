"""
Task Dependency Scheduler
-------------------------

Implements the design described in ``TASK_DEPENDENCY_DESIGN.md``.
Provides:

* ``DependencyGraph`` – a directed‑acyclic graph (DAG) that stores tasks
  and their dependencies.
* ``TaskScheduler`` – builds the graph, auto‑detects dependencies from
  free‑form task descriptions, schedules tasks respecting the DAG,
  runs independent tasks in parallel, blocks on unmet dependencies,
  and tracks progress with a simple textual visualization.

The scheduler is deliberately lightweight and uses only the Python
standard library so it can be imported from the read‑only
``grind_spawner.py`` without any external dependencies.

Typical usage (see the ``main`` block at the bottom of the file)::

    from task_scheduler import TaskScheduler

    # Define tasks (name -> callable)
    tasks = {
        "download_data": lambda: print("Downloading…"),
        "preprocess":    lambda: print("Pre‑processing…"),
        "train_model":   lambda: print("Training…"),
        "evaluate":      lambda: print("Evaluating…"),
    }

    # Free‑form description that may contain dependency hints
    description = '''
        preprocess depends on download_data
        train_model depends on preprocess
        evaluate depends on train_model
    '''

    scheduler = TaskScheduler(tasks)
    scheduler.auto_add_dependencies_from_text(description)
    scheduler.run()          # runs tasks respecting dependencies
"""

import re
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Set, Tuple


class DependencyGraph:
    """
    Simple directed‑acyclic graph implementation.
    * ``graph[task]`` – list of tasks that depend on ``task`` (out‑edges).
    * ``in_degree[task]`` – number of unmet prerequisites.
    """

    def __init__(self) -> None:
        self.graph: Dict[str, List[str]] = defaultdict(list)
        self.in_degree: Dict[str, int] = defaultdict(int)

    def add_task(self, task: str) -> None:
        """Register a task – ensures it appears in ``in_degree``."""
        self.in_degree.setdefault(task, 0)

    def add_dependency(self, task: str, depends_on: str) -> None:
        """
        Declare that ``task`` cannot start until ``depends_on`` finishes.
        Raises ``ValueError`` if the dependency would create a cycle.
        """
        if task == depends_on:
            raise ValueError(f"Task '{task}' cannot depend on itself")

        # Add nodes if they are new
        self.add_task(task)
        self.add_task(depends_on)

        # Record edge
        self.graph[depends_on].append(task)
        self.in_degree[task] += 1

        # Quick cycle detection (DFS from the new edge's target)
        if self._has_path(task, depends_on):
            raise ValueError(f"Adding dependency {task} -> {depends_on} creates a cycle")

    def _has_path(self, start: str, target: str, visited: Set[str] = None) -> bool:
        """Depth‑first search used for cycle detection."""
        if visited is None:
            visited = set()
        if start == target:
            return True
        visited.add(start)
        for nxt in self.graph.get(start, []):
            if nxt not in visited and self._has_path(nxt, target, visited):
                return True
        return False

    def independent_tasks(self) -> List[str]:
        """Return tasks whose ``in_degree`` is zero (ready to run)."""
        return [t for t, deg in self.in_degree.items() if deg == 0]

    def dependents(self, task: str) -> List[str]:
        """Tasks that directly depend on ``task``."""
        return self.graph.get(task, [])


class TaskScheduler:
    """
    High‑level orchestrator that:
    * builds a ``DependencyGraph`` from explicit calls or auto‑detection,
    * runs independent tasks in parallel (ThreadPoolExecutor),
    * blocks tasks until all prerequisites are satisfied,
    * prints a simple progress bar and a textual DAG visualisation.
    """

    DEP_REGEX = re.compile(
        r"(?P<task>\w+)\s+depends\s+on\s+(?P<dependency>\w+)",
        flags=re.IGNORECASE,
    )

    def __init__(self, tasks: Dict[str, Callable[[], None]]) -> None:
        """
        ``tasks`` – mapping ``task_name -> callable``.
        All callables must be thread‑safe (or be I/O bound – the scheduler
        uses a thread pool, not processes).
        """
        self.tasks = tasks
        self.graph = DependencyGraph()
        for name in tasks:
            self.graph.add_task(name)

        # Runtime bookkeeping
        self._completed: Set[str] = set()
        self._lock = threading.Lock()
        self._total = len(tasks)

    # ------------------------------------------------------------------
    # Dependency handling
    # ------------------------------------------------------------------
    def add_dependency(self, task: str, depends_on: str) -> None:
        """Public wrapper around ``DependencyGraph.add_dependency``."""
        self.graph.add_dependency(task, depends_on)

    def auto_add_dependencies_from_text(self, text: str) -> None:
        """
        Scan ``text`` for lines like ``taskX depends on taskY`` and add them.
        The detection is deliberately permissive – any occurrence of the
        pattern is interpreted as a dependency.
        """
        for match in self.DEP_REGEX.finditer(text):
            task = match.group("task")
            dep = match.group("dependency")
            if task not in self.tasks:
                raise KeyError(f"Detected unknown task '{task}' in description")
            if dep not in self.tasks:
                raise KeyError(f"Detected unknown dependency '{dep}' in description")
            self.add_dependency(task, dep)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _run_task(self, name: str) -> Tuple[str, Exception]:
        """Execute a single task and capture any exception."""
        try:
            self.tasks[name]()
            return name, None
        except Exception as exc:  # pragma: no cover – defensive
            return name, exc

    def _task_completed(self, name: str) -> None:
        """Mark ``name`` as finished and update downstream indegrees."""
        with self._lock:
            self._completed.add(name)
            for dependent in self.graph.dependents(name):
                self.graph.in_degree[dependent] -= 1

    def _print_progress(self) -> None:
        """Simple textual progress bar."""
        completed = len(self._completed)
        percent = (completed / self._total) * 100
        bar_len = 40
        filled = int(bar_len * completed / self._total)
        bar = "=" * filled + "-" * (bar_len - filled)
        print(f"\rProgress: [{bar}] {completed}/{self._total} ({percent:.1f}%)", end="")

    def _visualise_graph(self) -> None:
        """Print a minimal adjacency‑list representation."""
        print("\nDependency graph:")
        for node in self.graph.in_degree:
            deps = self.graph.dependents(node)
            if deps:
                print(f"  {node} -> {', '.join(deps)}")
            else:
                print(f"  {node} (no dependents)")

    def run(self, max_workers: int = None) -> None:
        """
        Execute all tasks respecting dependencies.

        * Independent tasks are submitted to a ``ThreadPoolExecutor``.
        * As soon as a task finishes, its dependents may become eligible
          and are submitted immediately.
        * The method blocks until every task has completed (or raised).
        """
        self._visualise_graph()
        print("\nStarting execution...")

        # Use a thread pool – default to number of CPUs if not supplied.
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Mapping of Future -> task name
            future_to_task: Dict[threading.Future, str] = {}

            # Submit all currently independent tasks
            for name in self.graph.independent_tasks():
                future = executor.submit(self._run_task, name)
                future_to_task[future] = name

            while future_to_task:
                # Wait for the next completed future
                done, _ = as_completed(future_to_task, timeout=None, return_when='FIRST_COMPLETED')
                for future in done:
                    task_name = future_to_task.pop(future)
                    result_name, exc = future.result()
                    assert result_name == task_name  # sanity

                    if exc:
                        # Propagate the first exception – abort everything
                        print(f"\nTask '{task_name}' failed with exception: {exc}")
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise exc

                    # Mark completion and possibly unlock new tasks
                    self._task_completed(task_name)
                    self._print_progress()

                    # Enqueue newly ready tasks
                    for candidate in self.graph.independent_tasks():
                        if candidate not in self._completed and candidate not in future_to_task.values():
                            fut = executor.submit(self._run_task, candidate)
                            future_to_task[fut] = candidate

        # Final newline after progress bar
        print("\nAll tasks completed successfully.\n")

    # ------------------------------------------------------------------
    # Integration helper for ``grind_spawner.py``
    # ------------------------------------------------------------------
    def schedule_and_spawn(self, spawner_callable: Callable[[str], None]) -> None:
        """
        Compatibility shim for the existing ``grind_spawner.py`` workflow.

        ``spawner_callable`` is expected to accept a single argument – the
        name of the task to spawn – and to perform whatever bookkeeping
        ``grind_spawner`` normally does (e.g. logging, resource allocation).

        The method runs the tasks in the same order as ``run()``, but
        delegates the actual execution to ``spawner_callable`` instead of
        calling the task's Python function directly.
        """
        self._visualise_graph()
        print("\nSpawning tasks via grind_spawner...")

        with ThreadPoolExecutor() as executor:
            future_to_task: Dict[threading.Future, str] = {}

            for name in self.graph.independent_tasks():
                future = executor.submit(spawner_callable, name)
                future_to_task[future] = name

            while future_to_task:
                done, _ = as_completed(future_to_task, timeout=None, return_when='FIRST_COMPLETED')
                for future in done:
                    task_name = future_to_task.pop(future)
                    # If the spawner raised, propagate
                    exc = future.exception()
                    if exc:
                        print(f"\nSpawner for task '{task_name}' raised: {exc}")
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise exc

                    self._task_completed(task_name)
                    self._print_progress()

                    for candidate in self.graph.independent_tasks():
                        if candidate not in self._completed and candidate not in future_to_task.values():
                            fut = executor.submit(spawner_callable, candidate)
                            future_to_task[fut] = candidate

        print("\nAll spawned tasks finished.\n")


# ----------------------------------------------------------------------
# Example usage (executed only when run as a script)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Dummy task functions for demonstration
    def dummy(name: str):
        import time, random
        time.sleep(random.uniform(0.2, 0.6))
        print(f"\n>>> {name} done")

    example_tasks = {
        "download": lambda: dummy("download"),
        "preprocess": lambda: dummy("preprocess"),
        "train": lambda: dummy("train"),
        "evaluate": lambda: dummy("evaluate"),
    }

    description = """
        preprocess depends on download
        train depends on preprocess
        evaluate depends on train
    """

    scheduler = TaskScheduler(example_tasks)
    scheduler.auto_add_dependencies_from_text(description)
    scheduler.run()