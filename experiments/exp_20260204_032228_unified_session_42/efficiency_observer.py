"""
efficiency_observer.py

Utility module that records runtime efficiency metrics for the Swarm architecture.
It tracks:

* llm_calls_per_task – number of LLM invocations per logical task
* tokens_per_task   – cumulative input+output tokens per task
* tool_hits/misses  – how often a tool was successfully used vs. fallback
* component_assemblies – count of component compositions performed
* full_builds       – number of full system builds triggered
* failure_patterns  – recurring exception signatures
* cost_per_task     – estimated monetary cost per task (based on token usage)

When repetitive LLM call patterns are detected, the observer can suggest
creating a dedicated tool to encapsulate that behaviour.
"""

from __future__ import annotations

import collections
import datetime
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Counter, DefaultDict, Dict, List, Tuple

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #
@dataclass
class LLMCallRecord:
    """A single LLM invocation."""
    model: str
    prompt: str
    response: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.utcnow)


@dataclass
class TaskMetrics:
    """Aggregated metrics for a single logical task."""
    task_id: str
    llm_calls: List[LLMCallRecord] = field(default_factory=list)
    tool_hits: int = 0
    tool_misses: int = 0
    component_assemblies: int = 0
    full_builds: int = 0
    failures: List[Tuple[str, str]] = field(default_factory=list)  # (exception_type, message)

    @property
    def total_llm_calls(self) -> int:
        return len(self.llm_calls)

    @property
    def total_input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.llm_calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.llm_calls)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """Very rough cost model – can be overridden by the host app."""
        # Example pricing (USD per 1k tokens)
        pricing = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
        }
        # Assume the model used most often for the task dominates cost
        if not self.llm_calls:
            return 0.0
        model_counter = collections.Counter(c.model for c in self.llm_calls)
        dominant_model, _ = model_counter.most_common(1)[0]
        price_per_k = pricing.get(dominant_model, 0.005)  # fallback price
        return (self.total_tokens / 1000.0) * price_per_k


# --------------------------------------------------------------------------- #
# Core observer
# --------------------------------------------------------------------------- #
class EfficiencyObserver:
    """
    Centralised observer that can be instantiated once per Swarm run.
    It is deliberately lightweight – all data lives in memory and can be
    flushed to JSON for later analysis.
    """

    def __init__(self) -> None:
        # Mapping from task_id -> TaskMetrics
        self._tasks: Dict[str, TaskMetrics] = {}
        # Global counters for quick look‑ups
        self._global_llm_calls: Counter[Tuple[str, str]] = collections.Counter()
        # Pattern detection cache – maps (model, prompt_hash) -> occurrence count
        self._prompt_signature_counter: Counter[Tuple[str, int]] = collections.Counter()
        # Settings
        self.repetition_threshold: int = 5  # when to suggest a new tool
        self._suggestions: List[str] = []

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def start_task(self, task_id: str) -> None:
        """Create a new task entry if it does not exist."""
        if task_id not in self._tasks:
            self._tasks[task_id] = TaskMetrics(task_id=task_id)
            logger.debug("Started tracking task %s", task_id)

    def record_llm_call(
        self,
        task_id: str,
        model: str,
        prompt: str,
        response: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """Record an LLM invocation belonging to a task."""
        self.start_task(task_id)

        record = LLMCallRecord(
            model=model,
            prompt=prompt,
            response=response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        task = self._tasks[task_id]
        task.llm_calls.append(record)

        # Global aggregation
        self._global_llm_calls[(model, self._hash_prompt(prompt))] += 1
        self._prompt_signature_counter[(model, self._hash_prompt(prompt))] += 1

        logger.debug(
            "Task %s – recorded LLM call %s (tokens=%d+%d)",
            task_id,
            model,
            input_tokens,
            output_tokens,
        )

        # Check for repetitive patterns
        self._maybe_add_suggestion(model, prompt)

    def record_tool_use(self, task_id: str, hit: bool = True) -> None:
        """Increment hit/miss counters for a tool usage."""
        self.start_task(task_id)
        if hit:
            self._tasks[task_id].tool_hits += 1
        else:
            self._tasks[task_id].tool_misses += 1
        logger.debug("Task %s – tool %s", task_id, "hit" if hit else "miss")

    def record_component_assembly(self, task_id: str) -> None:
        """Increment component assembly count."""
        self.start_task(task_id)
        self._tasks[task_id].component_assemblies += 1
        logger.debug("Task %s – component assembly recorded", task_id)

    def record_full_build(self, task_id: str) -> None:
        """Increment full build count."""
        self.start_task(task_id)
        self._tasks[task_id].full_builds += 1
        logger.debug("Task %s – full build recorded", task_id)

    def record_failure(self, task_id: str, exc: BaseException) -> None:
        """Capture a failure pattern."""
        self.start_task(task_id)
        exc_type = type(exc).__name__
        message = str(exc)
        self._tasks[task_id].failures.append((exc_type, message))
        logger.debug("Task %s – failure recorded: %s: %s", task_id, exc_type, message)

    # ------------------------------------------------------------------- #
    # Query / Reporting
    # ------------------------------------------------------------------- #
    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        """Return a dictionary with aggregated metrics for a given task."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not tracked")
        t = self._tasks[task_id]
        return {
            "task_id": task_id,
            "llm_calls": t.total_llm_calls,
            "tokens": t.total_tokens,
            "cost_usd": round(t.estimated_cost_usd, 6),
            "tool_hits": t.tool_hits,
            "tool_misses": t.tool_misses,
            "component_assemblies": t.component_assemblies,
            "full_builds": t.full_builds,
            "failure_patterns": t.failures,
        }

    def get_global_summary(self) -> Dict[str, Any]:
        """Aggregate metrics across all tasks."""
        total_llm_calls = sum(t.total_llm_calls for t in self._tasks.values())
        total_tokens = sum(t.total_tokens for t in self._tasks.values())
        total_cost = sum(t.estimated_cost_usd for t in self._tasks.values())
        total_hits = sum(t.tool_hits for t in self._tasks.values())
        total_misses = sum(t.tool_misses for t in self._tasks.values())

        # Simple failure histogram
        failure_counter: Counter[Tuple[str, str]] = collections.Counter()
        for t in self._tasks.values():
            failure_counter.update(t.failures)

        return {
            "total_tasks": len(self._tasks),
            "total_llm_calls": total_llm_calls,
            "total_tokens": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "tool_hits": total_hits,
            "tool_misses": total_misses,
            "failure_histogram": dict(failure_counter),
        }

    def get_suggestions(self) -> List[str]:
        """Return any tool‑creation suggestions generated so far."""
        return list(self._suggestions)

    # ------------------------------------------------------------------- #
    # Persistence
    # ------------------------------------------------------------------- #
    def dump_to_json(self, path: str) -> None:
        """Serialise the whole observer state to a JSON file."""
        data = {
            "tasks": {
                tid: {
                    "llm_calls": [
                        {
                            "model": c.model,
                            "prompt_hash": self._hash_prompt(c.prompt),
                            "input_tokens": c.input_tokens,
                            "output_tokens": c.output_tokens,
                            "timestamp": c.timestamp.isoformat(),
                        }
                        for c in tm.llm_calls
                    ],
                    "tool_hits": tm.tool_hits,
                    "tool_misses": tm.tool_misses,
                    "component_assemblies": tm.component_assemblies,
                    "full_builds": tm.full_builds,
                    "failures": tm.failures,
                }
                for tid, tm in self._tasks.items()
            },
            "global_llm_calls": {
                f"{model}|{prompt_hash}": count
                for (model, prompt_hash), count in self._global_llm_calls.items()
            },
            "suggestions": self._suggestions,
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
        logger.info("EfficiencyObserver state dumped to %s", path)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    @staticmethod
    def _hash_prompt(prompt: str) -> int:
        """Deterministic lightweight hash for prompt signatures."""
        # Using built‑in hash with fixed seed for reproducibility across runs
        return hash(prompt) & 0xFFFFFFFF

    def _maybe_add_suggestion(self, model: str, prompt: str) -> None:
        """If a prompt repeats enough times, suggest extracting it as a tool."""
        signature = (model, self._hash_prompt(prompt))
        count = self._prompt_signature_counter[signature]
        if count == self.repetition_threshold:
            suggestion = (
                f"Prompt used {count} times with model {model}. "
                "Consider encapsulating this pattern into a custom tool."
            )
            self._suggestions.append(suggestion)
            logger.info("EfficiencyObserver suggestion added: %s", suggestion)

    # ------------------------------------------------------------------- #
    # Convenience static constructor
    # ------------------------------------------------------------------- #
    @classmethod
    def default(cls) -> "EfficiencyObserver":
        """Factory that returns a pre‑configured observer."""
        observer = cls()
        # Adjust thresholds or pricing here if needed
        observer.repetition_threshold = 5
        return observer


# --------------------------------------------------------------------------- #
# Example usage (removed in production; kept as docstring for developers)
# --------------------------------------------------------------------------- #
"""
observer = EfficiencyObserver.default()

observer.record_llm_call(
    task_id="task-123",
    model="gpt-4",
    prompt="Summarize the following text...",
    response="...",
    input_tokens=120,
    output_tokens=45,
)

observer.record_tool_use("task-123", hit=True)
observer.record_failure("task-123", ValueError("Invalid input"))

print(observer.get_task_summary("task-123"))
print(observer.get_global_summary())
print(observer.get_suggestions())
"""