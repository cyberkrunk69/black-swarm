"""
Task Dependency Scheduler (TDS)

Implements the design described in TASK_DEPENDENCY_DESIGN.md.
- Parses free‑form task descriptions to auto‑detect dependencies.
- Builds a directed acyclic graph (DAG) of tasks.
- Executes independent tasks in parallel (via ThreadPoolExecutor).
- Blocks execution of a task until all its dependencies have completed.
- Tracks progress and provides a simple textual visualization of the DAG.
- Provides a thin integration hook for ``grind_spawner.py`` (read‑only core file).

Author: EXECUTION worker
"""

import re
import threading
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Set, Tuple

# --------------------------------------------------------------------------- #
# Dependency graph utilities
# --------------------------------------------------------------------------- #
class DependencyGraph:
    """
    Directed Acyclic Graph (DAG) representing task dependencies.
    Nodes are task identifiers (strings). Edges point from a dependency
    to the dependent task.
    """

    _DEP_PATTERN = re.compile(r"depends\s+on\s+([A-Za-z0-9_\-]+)", re.IGNORECASE)

    def __init__(self) -> None:
        self._adjacency: Dict[str, List[str]] = defaultdict(list)   # dep -> [dependents]
        self._in_degree: Dict[str, int] = defaultdict(int)         # task -> number of unmet deps
        self._tasks: Set[str] = set()

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def add_task(self, task_id: str) -> None:
        """Register a task in the graph (idempotent)."""
        if task_id not in self._tasks:
            self._tasks.add(task_id)
            self._in_degree.setdefault(task_id, 0)

    def add_dependency(self, task_id: str, depends_on: str) -> None:
        """Add an edge ``depends_on -> task_id``."""
        self.add_task(task_id)
        self.add_task(depends_on)
        self._adjacency[depends_on].append(task_id)
        self._in_degree[task_id] += 1

    def get_independent_tasks(self) -> List[str]:
        """Return tasks with zero unmet dependencies."""
        return [t for t in self._tasks if self._in_degree[t] == 0]

    def dependents_of(self, task_id: str) -> List[str]:
        """Return tasks that directly depend on ``task_id``."""
        return self._adjacency.get(task_id, [])

    def topological_order(self) -> List[str]:
        """
        Return a topological ordering of tasks.
        Raises RuntimeError if a cycle is detected.
        """
        in_deg = self._in_degree.copy()
        q = deque([t for t in self._tasks if in_deg[t] == 0])
        order = []

        while q:
            node = q.popleft()
            order.append(node)
            for dep in self.dependents_of(node):
                in_deg[dep] -= 1
                if in_deg[dep] == 0:
                    q.append(dep)

        if len(order) != len(self._tasks):
            raise RuntimeError("Cyclic dependency detected in task graph.")
        return order

    # ------------------------------------------------------------------- #
    # Dependency detection helpers
    # ------------------------------------------------------------------- #
    @classmethod
    def parse_dependencies_from_text(cls, text: str) -> List[str]:
        """
        Very simple heuristic: look for lines containing the phrase
        ``depends on <TASK_ID>`` (case‑insensitive). Returns a list of
        extracted task identifiers.
        """
        deps = []
        for line in text.splitlines():
            match = cls._DEP_PATTERN.search(line)
            if match:
                deps.append(match.group(1).strip())
        return deps

    # ------------------------------------------------------------------- #
    # Visualization
    # ------------------------------------------------------------------- #
    def visualize(self) -> str:
        """
        Produce a minimal ASCII representation of the DAG.
        Example:
            A
            ├─> B
            └─> C
                └─> D
        """
        lines = []
        visited = set()

        def dfs(node: str, prefix: str = ""):
            lines.append(f"{prefix}{node}")
            visited.add(node)
            children = self.dependents_of(node)
            for i, child in enumerate(children):
                connector = "└─> " if i == len(children) - 1 else "├─> "
                child_prefix = prefix + ("    " if i == len(children) - 1 else "│   ")
                dfs(child, prefix + connector)

        # start from roots (independent tasks)
        roots = self.get_independent_tasks()
        for i, root in enumerate(roots):
            dfs(root, "")

        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Scheduler
# --------------------------------------------------------------------------- #
class TaskScheduler:
    """
    Orchestrates execution of tasks respecting dependencies.
    Users supply a mapping ``task_id -> (callable, description)`` where
    ``callable`` is a zero‑argument function that performs the work.
    The description (string) is used for dependency auto‑detection.
    """

    def __init__(self, max_workers: int = None):
        self.graph = DependencyGraph()
        self._tasks: Dict[str, Tuple[Callable[[], None], str]] = {}
        self._max_workers = max_workers or (threading.cpu_count() or 4)

        # Runtime state
        self._completed: Set[str] = set()
        self._lock = threading.Lock()
        self._progress_callback = None  # optional user‑provided hook

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def register_task(self, task_id: str, func: Callable[[], None], description: str = "") -> None:
        """
        Register a task with its execution function and a free‑form description.
        The description is scanned for ``depends on <TASK_ID>`` statements.
        """
        if task_id in self._tasks:
            raise ValueError(f"Task '{task_id}' already registered.")
        self._tasks[task_id] = (func, description)
        self.graph.add_task(task_id)

        # Auto‑detect dependencies from description
        for dep in self.graph.parse_dependencies_from_text(description):
            self.graph.add_dependency(task_id, dep)

    def set_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """
        Optional hook called after each task finishes.
        Signature: ``callback(task_id, completed_count, total_count)``.
        """
        self._progress_callback = callback

    def run(self) -> List[str]:
        """
        Execute all registered tasks respecting dependencies.
        Returns the order in which tasks completed.
        """
        # Validate DAG (detect cycles early)
        self.graph.topological_order()  # will raise if cyclic

        total_tasks = len(self._tasks)
        completed_order: List[str] = []

        # Queue of ready‑to‑run tasks (zero unmet deps)
        ready = deque(self.graph.get_independent_tasks())

        # Mapping task_id -> Future (for awaiting)
        futures: Dict[str, threading.Event] = {}

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            while ready or futures:
                # Submit all currently ready tasks
                while ready:
                    task_id = ready.popleft()
                    func, _ = self._tasks[task_id]
                    event = threading.Event()
                    futures[task_id] = event

                    def _run(tid: str, f: Callable[[], None], ev: threading.Event):
                        try:
                            f()
                        finally:
                            ev.set()  # signal completion

                    executor.submit(_run, task_id, func, event)

                # Wait for any task to finish
                done_task_id = None
                for tid, ev in list(futures.items()):
                    if ev.wait(timeout=0.1):  # non‑blocking poll
                        done_task_id = tid
                        break

                if done_task_id is None:
                    continue  # no task finished yet; loop again

                # Clean up finished task
                del futures[done_task_id]
                with self._lock:
                    self._completed.add(done_task_id)
                    completed_order.append(done_task_id)

                # Progress callback
                if self._progress_callback:
                    self._progress_callback(done_task_id, len(self._completed), total_tasks)

                # Enqueue dependents whose dependencies are now satisfied
                for dependent in self.graph.dependents_of(done_task_id):
                    # All dependencies of `dependent` must be in self._completed
                    deps_satisfied = all(
                        dep in self._completed for dep in self._incoming_edges(dependent)
                    )
                    if deps_satisfied and dependent not in self._completed and dependent not in futures:
                        ready.append(dependent)

        return completed_order

    # ------------------------------------------------------------------- #
    # Helper utilities
    # ------------------------------------------------------------------- #
    def _incoming_edges(self, task_id: str) -> List[str]:
        """Return list of tasks that `task_id` depends on."""
        incoming = []
        for src, targets in self.graph._adjacency.items():
            if task_id in targets:
                incoming.append(src)
        return incoming

    def visualize(self) -> str:
        """Expose the graph's ASCII visualization."""
        return self.graph.visualize()

    # ------------------------------------------------------------------- #
    # Integration with grind_spawner.py (read‑only core file)
    # ------------------------------------------------------------------- #
    def integrate_with_grind_spawner(self) -> None:
        """
        The core system provides ``grind_spawner.spawn(task_id, func)``.
        This method registers each task with the spawner so that external
        tooling can trigger them individually if needed.
        """
        try:
            from grind_spawner import spawn  # type: ignore
        except Exception as exc:
            raise RuntimeError("Failed to import grind_spawner.spawn") from exc

        for task_id, (func, _) in self._tasks.items():
            spawn(task_id, func)


# --------------------------------------------------------------------------- #
# Example usage (removed in production; kept for reference)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simple demo showing auto‑detection and parallel execution
    import time

    def work(name, secs):
        def _inner():
            print(f"Starting {name}")
            time.sleep(secs)
            print(f"Finished {name}")
        return _inner

    scheduler = TaskScheduler()

    scheduler.register_task(
        "A",
        work("A", 2),
        description="Root task, no dependencies."
    )
    scheduler.register_task(
        "B",
        work("B", 1),
        description="depends on A"
    )
    scheduler.register_task(
        "C",
        work("C", 1.5),
        description="depends on A"
    )
    scheduler.register_task(
        "D",
        work("D", 0.5),
        description="depends on B\ndepends on C"
    )

    print("Dependency graph:")
    print(scheduler.visualize())

    order = scheduler.run()
    print("Execution order:", order)