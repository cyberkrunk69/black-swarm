"""
task_scheduler.py

Implements a lightweight dependency‑aware task scheduler that can be
imported by ``grind_spawner.py`` (or any other component) to execute
tasks in parallel while respecting explicit or automatically‑detected
dependencies.

Key components
---------------
* **DependencyGraph** – stores a directed acyclic graph (DAG) of tasks.
  Provides methods for adding tasks, adding edges, detecting cycles,
  and visualising the graph (textual representation).

* **TaskScheduler** – consumes a list of raw task specifications,
  builds a ``DependencyGraph`` (auto‑detecting dependencies from the
  task description text), and executes the tasks using a thread pool.
  The scheduler blocks tasks whose dependencies have not yet completed,
  updates progress counters and prints a simple progress bar.

* **Auto‑dependency detection** – looks for the pattern
  ``depends on <TASK_NAME>`` (case‑insensitive) inside the free‑form
  task description.  If found, a directed edge ``<TASK_NAME> -> <CURRENT>`` is
  added to the graph.

* **Integration hook** – the module exposes a ``create_scheduler`` factory
  that ``grind_spawner.py`` can import and call with its list of tasks.

The implementation purposefully avoids external heavy dependencies;
only the Python standard library is used.  If a richer visualisation
(e.g. GraphViz) is desired, the ``visualise`` method can be extended.

"""

import re
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Iterable, List, Set, Tuple, Any


# ----------------------------------------------------------------------
# DependencyGraph
# ----------------------------------------------------------------------
class DependencyGraph:
    """
    Directed acyclic graph (DAG) representing task dependencies.

    Nodes are task identifiers (strings).  Edges point from a prerequisite
    task to a dependent task.
    """

    _DEP_PATTERN = re.compile(r"depends\s+on\s+([A-Za-z0-9_\-]+)", re.IGNORECASE)

    def __init__(self) -> None:
        # adjacency list: prerequisite -> set(dependents)
        self._adj: Dict[str, Set[str]] = defaultdict(set)
        # reverse adjacency: dependent -> set(prerequisites)
        self._rev_adj: Dict[str, Set[str]] = defaultdict(set)
        self._nodes: Set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_task(self, task_id: str) -> None:
        """Register a task node (idempotent)."""
        self._nodes.add(task_id)
        # Ensure empty adjacency entries exist
        self._adj.setdefault(task_id, set())
        self._rev_adj.setdefault(task_id, set())

    def add_dependency(self, prerequisite: str, dependent: str) -> None:
        """
        Add a directed edge prerequisite -> dependent.
        Raises ValueError if the edge would introduce a cycle.
        """
        if prerequisite == dependent:
            raise ValueError(f"Task '{task_id}' cannot depend on itself.")

        # Ensure nodes exist
        self.add_task(prerequisite)
        self.add_task(dependent)

        # Temporarily add edge and test for cycles
        self._adj[prerequisite].add(dependent)
        self._rev_adj[dependent].add(prerequisite)

        if self._has_cycle():
            # rollback
            self._adj[prerequisite].remove(dependent)
            self._rev_adj[dependent].remove(prerequisite)
            raise ValueError(
                f"Adding dependency {prerequisite} -> {dependent} would create a cycle."
            )

    def dependencies_of(self, task_id: str) -> Set[str]:
        """Return the set of direct prerequisites for ``task_id``."""
        return set(self._rev_adj.get(task_id, set()))

    def dependents_of(self, task_id: str) -> Set[str]:
        """Return the set of direct dependents for ``task_id``."""
        return set(self._adj.get(task_id, set()))

    def all_tasks(self) -> Set[str]:
        """Return all task identifiers known to the graph."""
        return set(self._nodes)

    def topological_order(self) -> List[str]:
        """
        Return a list of tasks in a valid topological order.
        Raises ValueError if a cycle is detected.
        """
        in_degree: Dict[str, int] = {n: 0 for n in self._nodes}
        for prereq, dependents in self._adj.items():
            for dep in dependents:
                in_degree[dep] += 1

        queue = deque([n for n, deg in in_degree.items() if deg == 0])
        order: List[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for dep in self._adj[node]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        if len(order) != len(self._nodes):
            raise ValueError("Cycle detected in dependency graph.")
        return order

    def visualise(self) -> str:
        """
        Return a simple textual representation of the graph.
        Example:
            TaskA
            └─> TaskB
            └─> TaskC
                └─> TaskD
        """
        lines: List[str] = []
        visited: Set[str] = set()

        def _dfs(node: str, prefix: str = "") -> None:
            lines.append(f"{prefix}{node}")
            visited.add(node)
            children = sorted(self._adj[node])
            for i, child in enumerate(children):
                connector = "└─> " if i == len(children) - 1 else "├─> "
                _dfs(child, prefix + connector)

        # start from roots (no incoming edges)
        roots = [n for n in self._nodes if not self._rev_adj[n]]
        for root in sorted(roots):
            _dfs(root)

        # include any orphaned nodes not reachable from roots
        for node in sorted(self._nodes - visited):
            lines.append(node)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _has_cycle(self) -> bool:
        """Detect a cycle using Kahn's algorithm."""
        try:
            self.topological_order()
            return False
        except ValueError:
            return True

    @classmethod
    def detect_dependencies_from_text(cls, text: str) -> Set[str]:
        """
        Scan ``text`` for ``depends on <TASK_ID>`` patterns.
        Returns a set of discovered task identifiers.
        """
        matches = cls._DEP_PATTERN.findall(text)
        return set(matches)


# ----------------------------------------------------------------------
# TaskScheduler
# ----------------------------------------------------------------------
class TaskScheduler:
    """
    Executes a collection of tasks respecting their dependencies.

    Parameters
    ----------
    tasks : Iterable[Dict]
        Each task dict must contain at least:
            - ``id``   : unique identifier (string)
            - ``func`` : callable to execute (no args) or ``callable(task)``.
            - ``text`` : free‑form description used for auto‑dependency detection.
    max_workers : int, optional
        Number of threads for parallel execution.  Defaults to ``min(32,
        os.cpu_count() + 4)`` (same default as ThreadPoolExecutor).
    """

    def __init__(self, tasks: Iterable[Dict[str, Any]], max_workers: int = None):
        self._raw_tasks = {t["id"]: t for t in tasks}
        self._graph = DependencyGraph()
        self._build_graph()
        self._max_workers = max_workers
        self._lock = threading.Lock()
        self._completed: Set[str] = set()
        self._total = len(self._raw_tasks)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """
        Execute all tasks, returning a mapping ``task_id -> result``.
        Raises RuntimeError if any task fails; the exception is re‑raised
        after all running tasks have been allowed to finish.
        """
        results: Dict[str, Any] = {}
        errors: List[Tuple[str, BaseException]] = []

        # Determine initial ready queue (tasks with no prerequisites)
        ready = deque([tid for tid in self._graph.all_tasks()
                       if not self._graph.dependencies_of(tid)])

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Map of future -> task_id
            future_to_id: Dict[Any, str] = {}

            # Helper to submit a task
            def submit_task(tid: str) -> None:
                func = self._raw_tasks[tid]["func"]
                # Normalise callable signature: allow zero‑arg or (task) arg
                if callable(func):
                    try:
                        # Peek signature length (quick heuristic)
                        if func.__code__.co_argcount == 0:
                            future = executor.submit(func)
                        else:
                            future = executor.submit(func, self._raw_tasks[tid])
                    except Exception as exc:
                        # Fallback – submit as zero‑arg
                        future = executor.submit(func)
                else:
                    raise TypeError(f"Task '{tid}' does not have a callable 'func'.")
                future_to_id[future] = tid

            # Prime the executor with the initial ready tasks
            while ready:
                tid = ready.popleft()
                submit_task(tid)

            # Process completed futures
            while future_to_id:
                for future in as_completed(future_to_id):
                    tid = future_to_id.pop(future)
                    try:
                        result = future.result()
                        results[tid] = result
                        self._mark_completed(tid)
                    except BaseException as exc:
                        errors.append((tid, exc))
                        # Continue processing other futures; we will raise later

                    # Enqueue newly unblocked tasks
                    newly_ready = self._unblocked_tasks(tid)
                    for nr in newly_ready:
                        submit_task(nr)

                    # Update progress UI
                    self._print_progress()
                    # Break to re‑enter as_completed loop with updated dict
                    break

        # After the executor shuts down, raise if any errors occurred
        if errors:
            err_msgs = "\n".join(f"{tid}: {repr(exc)}" for tid, exc in errors)
            raise RuntimeError(f"One or more tasks failed:\n{err_msgs}")

        return results

    def visualise(self) -> str:
        """Proxy to the underlying graph visualisation."""
        return self._graph.visualise()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_graph(self) -> None:
        """Populate the DependencyGraph from raw tasks, auto‑detecting deps."""
        # Register all nodes first
        for task_id in self._raw_tasks:
            self._graph.add_task(task_id)

        # Add explicit dependencies if present, else auto‑detect
        for task_id, spec in self._raw_tasks.items():
            # Explicit list (optional)
            explicit = spec.get("depends_on", [])
            # Auto‑detect from description text
            auto = DependencyGraph.detect_dependencies_from_text(spec.get("text", ""))

            all_deps = set(explicit) | auto
            for dep in all_deps:
                if dep not in self._raw_tasks:
                    raise ValueError(
                        f"Task '{task_id}' declares dependency on unknown task '{dep}'."
                    )
                self._graph.add_dependency(dep, task_id)

    def _mark_completed(self, task_id: str) -> None:
        with self._lock:
            self._completed.add(task_id)

    def _unblocked_tasks(self, just_finished: str) -> List[str]:
        """
        Return a list of tasks that have become ready because all their
        prerequisites are now completed.
        """
        ready: List[str] = []
        for dependent in self._graph.dependents_of(just_finished):
            deps = self._graph.dependencies_of(dependent)
            if deps.issubset(self._completed) and dependent not in self._completed:
                ready.append(dependent)
        return ready

    def _print_progress(self) -> None:
        completed = len(self._completed)
        pct = (completed / self._total) * 100
        bar_len = 40
        filled_len = int(bar_len * completed / self._total)
        bar = "=" * filled_len + "-" * (bar_len - filled_len)
        print(f"\rProgress: [{bar}] {completed}/{self._total} ({pct:.1f}%)", end="", flush=True)
        if completed == self._total:
            print()  # newline at completion


# ----------------------------------------------------------------------
# Factory for external integration (e.g., grind_spawner.py)
# ----------------------------------------------------------------------
def create_scheduler(task_definitions: Iterable[Dict[str, Any]], max_workers: int = None) -> TaskScheduler:
    """
    Convenience wrapper used by external modules.

    Example usage in ``grind_spawner.py``:

        from task_scheduler import create_scheduler

        scheduler = create_scheduler(tasks, max_workers=8)
        results = scheduler.run()
    """
    return TaskScheduler(task_definitions, max_workers=max_workers)