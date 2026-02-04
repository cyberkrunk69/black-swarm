"""
efficiency_observer.py

Utility to observe and record efficiency related metrics for the Swarm architecture.
Tracks:
- llm_calls_per_task
- tokens_per_task
- tool_hits / tool_misses
- component_assemblies
- full_builds
- failure_patterns
- cost_per_task

Provides a simple recommendation engine that suggests creating a reusable tool
when identical LLM calls are observed repeatedly across tasks.
"""

import threading
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class LLMCallRecord:
    """Record for a single LLM invocation."""
    model: str
    prompt: str
    response: str
    tokens_used: int
    cost_usd: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskMetrics:
    """Aggregated metrics for a single high‑level task."""
    llm_calls: List[LLMCallRecord] = field(default_factory=list)
    tool_hits: int = 0
    tool_misses: int = 0
    component_assemblies: int = 0
    full_builds: int = 0
    failures: List[str] = field(default_factory=list)  # store failure messages / patterns

    @property
    def total_tokens(self) -> int:
        return sum(call.tokens_used for call in self.llm_calls)

    @property
    def total_cost(self) -> float:
        return sum(call.cost_usd for call in self.llm_calls)

    @property
    def llm_call_count(self) -> int:
        return len(self.llm_calls)


class EfficiencyObserver:
    """Singleton observer that aggregates efficiency data across tasks."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EfficiencyObserver, cls).__new__(cls)
                cls._instance._init_internal()
            return cls._instance

    def _init_internal(self):
        self._task_data: Dict[str, TaskMetrics] = {}
        self._global_llm_call_counter: Counter = Counter()
        self._repeat_llm_calls: Dict[Tuple[str, str], List[float]] = defaultdict(list)
        # (model, prompt) -> timestamps list
        self._recommendations: List[str] = []

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #

    def start_task(self, task_id: str) -> None:
        """Initialize metrics for a new task."""
        with self._lock:
            if task_id in self._task_data:
                # Reset if re‑started
                self._task_data[task_id] = TaskMetrics()
            else:
                self._task_data[task_id] = TaskMetrics()

    def record_llm_call(
        self,
        task_id: str,
        model: str,
        prompt: str,
        response: str,
        tokens_used: int,
        cost_usd: float,
    ) -> None:
        """Record an LLM invocation for a given task."""
        record = LLMCallRecord(
            model=model,
            prompt=prompt,
            response=response,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
        )
        key = (model, prompt)

        with self._lock:
            task = self._task_data.setdefault(task_id, TaskMetrics())
            task.llm_calls.append(record)

            # Global statistics
            self._global_llm_call_counter[key] += 1
            self._repeat_llm_calls[key].append(record.timestamp)

            # Check for repeat pattern (simple heuristic)
            if self._global_llm_call_counter[key] >= 3:
                self._maybe_suggest_tool_creation(key)

    def record_tool_hit(self, task_id: str) -> None:
        with self._lock:
            self._task_data.setdefault(task_id, TaskMetrics()).tool_hits += 1

    def record_tool_miss(self, task_id: str) -> None:
        with self._lock:
            self._task_data.setdefault(task_id, TaskMetrics()).tool_misses += 1

    def record_component_assembly(self, task_id: str) -> None:
        with self._lock:
            self._task_data.setdefault(task_id, TaskMetrics()).component_assemblies += 1

    def record_full_build(self, task_id: str) -> None:
        with self._lock:
            self._task_data.setdefault(task_id, TaskMetrics()).full_builds += 1

    def record_failure(self, task_id: str, pattern: str) -> None:
        """Log a failure pattern (e.g., exception message, error code)."""
        with self._lock:
            self._task_data.setdefault(task_id, TaskMetrics()).failures.append(pattern)

    # --------------------------------------------------------------------- #
    # Retrieval helpers
    # --------------------------------------------------------------------- #

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        return self._task_data.get(task_id)

    def get_overall_metrics(self) -> Dict[str, Any]:
        """Aggregate metrics across all observed tasks."""
        with self._lock:
            total_tasks = len(self._task_data)
            total_llm_calls = sum(t.llm_call_count for t in self._task_data.values())
            total_tokens = sum(t.total_tokens for t in self._task_data.values())
            total_cost = sum(t.total_cost for t in self._task_data.values())
            total_tool_hits = sum(t.tool_hits for t in self._task_data.values())
            total_tool_misses = sum(t.tool_misses for t in self._task_data.values())
            total_component_assemblies = sum(t.component_assemblies for t in self._task_data.values())
            total_full_builds = sum(t.full_builds for t in self._task_data.values())
            all_failures = [f for t in self._task_data.values() for f in t.failures]

            return {
                "total_tasks": total_tasks,
                "total_llm_calls": total_llm_calls,
                "total_tokens": total_tokens,
                "total_cost_usd": total_cost,
                "total_tool_hits": total_tool_hits,
                "total_tool_misses": total_tool_misses,
                "total_component_assemblies": total_component_assemblies,
                "total_full_builds": total_full_builds,
                "failure_patterns": Counter(all_failures),
                "repeat_llm_calls": dict(self._global_llm_call_counter),
            }

    # --------------------------------------------------------------------- #
    # Recommendation engine
    # --------------------------------------------------------------------- #

    def _maybe_suggest_tool_creation(self, key: Tuple[str, str]) -> None:
        """
        If the same LLM call (model + prompt) appears repeatedly, suggest
        extracting it into a reusable tool.

        The suggestion is added once per unique (model, prompt) pair when the
        threshold is first crossed.
        """
        model, prompt = key
        suggestion = (
            f"Consider creating a reusable tool for model '{model}' with the following prompt:\n"
            f"{prompt!r}\n"
            f"Observed {self._global_llm_call_counter[key]} identical calls across tasks."
        )
        if suggestion not in self._recommendations:
            self._recommendations.append(suggestion)

    def get_recommendations(self) -> List[str]:
        """Return accumulated efficiency improvement suggestions."""
        with self._lock:
            return list(self._recommendations)

    # --------------------------------------------------------------------- #
    # Debug / pretty printing
    # --------------------------------------------------------------------- #

    def __repr__(self) -> str:
        metrics = self.get_overall_metrics()
        return (
            f"<EfficiencyObserver tasks={metrics['total_tasks']} "
            f"llm_calls={metrics['total_llm_calls']} tokens={metrics['total_tokens']} "
            f"cost_usd={metrics['total_cost_usd']:.2f}>"
        )


# Convenience singleton instance for importers
observer = EfficiencyObserver()