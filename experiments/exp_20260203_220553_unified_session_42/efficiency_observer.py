"""
efficiency_observer.py

Utility for observing and reporting efficiency metrics across the Swarm architecture.
Tracks:

* llm_calls_per_task
* tokens_per_task
* tool_hits / tool_misses
* component_assemblies
* full_builds
* failure_patterns
* cost_per_task

Provides a simple suggestion engine: when the same LLM call (model + prompt) repeats
across tasks, it recommends extracting the call into a reusable tool.
"""

from __future__ import annotations

import json
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class LLMCallRecord:
    """Record of a single LLM invocation."""
    model: str
    prompt: str
    response_tokens: int
    input_tokens: int
    cost_usd: float
    timestamp: float
    # Additional optional metadata (e.g., temperature, top_p) can be stored here.
    meta: Dict[str, Any] = field(default_factory=dict)


class EfficiencyObserver:
    """
    Central observer for runtime efficiency metrics.

    The observer is thread‑safe and can be used from any part of the system.
    All data is kept in‑memory; a `dump` method can persist a JSON snapshot.
    """

    _instance: Optional["EfficiencyObserver"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EfficiencyObserver":
        # Singleton pattern – only one observer per process.
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_internal()
            return cls._instance

    # --------------------------------------------------------------------- #
    # Internal state initialisation
    # --------------------------------------------------------------------- #
    def _init_internal(self) -> None:
        # Mapping: task_id -> list of LLMCallRecord
        self._llm_calls: defaultdict[str, List[LLMCallRecord]] = defaultdict(list)

        # Counters for quick aggregates
        self._tool_hits: Counter = Counter()
        self._tool_misses: Counter = Counter()
        self._component_assemblies: Counter = Counter()
        self._full_builds: Counter = Counter()
        self._failure_patterns: Counter = Counter()
        self._cost_per_task: defaultdict[str, float] = defaultdict(float)

        # For suggestion engine
        self._prompt_signature_counter: Counter = Counter()
        self._signature_to_examples: defaultdict[
            str, List[Tuple[str, LLMCallRecord]]
        ] = defaultdict(list)

        # Thread safety for updates
        self._data_lock = threading.RLock()

    # --------------------------------------------------------------------- #
    # Public API – logging
    # --------------------------------------------------------------------- #
    def log_llm_call(
        self,
        task_id: str,
        model: str,
        prompt: str,
        input_tokens: int,
        response_tokens: int,
        cost_usd: float,
        timestamp: float,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an LLM call for a given task."""
        meta = meta or {}
        record = LLMCallRecord(
            model=model,
            prompt=prompt,
            input_tokens=input_tokens,
            response_tokens=response_tokens,
            cost_usd=cost_usd,
            timestamp=timestamp,
            meta=meta,
        )
        signature = self._make_signature(model, prompt)

        with self._data_lock:
            self._llm_calls[task_id].append(record)
            self._cost_per_task[task_id] += cost_usd
            self._prompt_signature_counter[signature] += 1
            self._signature_to_examples[signature].append((task_id, record))

    def log_tool_hit(self, tool_name: str) -> None:
        with self._data_lock:
            self._tool_hits[tool_name] += 1

    def log_tool_miss(self, tool_name: str) -> None:
        with self._data_lock:
            self._tool_misses[tool_name] += 1

    def log_component_assembly(self, component_name: str) -> None:
        with self._data_lock:
            self._component_assemblies[component_name] += 1

    def log_full_build(self, build_id: str) -> None:
        with self._data_lock:
            self._full_builds[build_id] += 1

    def log_failure(self, pattern: str) -> None:
        """Record a failure pattern (e.g., 'timeout', 'validation_error')."""
        with self._data_lock:
            self._failure_patterns[pattern] += 1

    # --------------------------------------------------------------------- #
    # Public API – queries
    # --------------------------------------------------------------------- #
    def llm_calls_per_task(self) -> Dict[str, int]:
        with self._data_lock:
            return {tid: len(calls) for tid, calls in self._llm_calls.items()}

    def tokens_per_task(self) -> Dict[str, int]:
        """Total tokens (input + output) consumed per task."""
        with self._data_lock:
            result: Dict[str, int] = {}
            for tid, calls in self._llm_calls.items():
                total = sum(c.input_tokens + c.response_tokens for c in calls)
                result[tid] = total
            return result

    def tool_hits(self) -> Dict[str, int]:
        with self._data_lock:
            return dict(self._tool_hits)

    def tool_misses(self) -> Dict[str, int]:
        with self._data_lock:
            return dict(self._tool_misses)

    def component_assemblies(self) -> Dict[str, int]:
        with self._data_lock:
            return dict(self._component_assemblies)

    def full_builds(self) -> Dict[str, int]:
        with self._data_lock:
            return dict(self._full_builds)

    def failure_patterns(self) -> Dict[str, int]:
        with self._data_lock:
            return dict(self._failure_patterns)

    def cost_per_task(self) -> Dict[str, float]:
        with self._data_lock:
            return dict(self._cost_per_task)

    # --------------------------------------------------------------------- #
    # Suggestion engine
    # --------------------------------------------------------------------- #
    def _make_signature(self, model: str, prompt: str) -> str:
        """
        Create a deterministic signature for a (model, prompt) pair.
        Whitespace is normalized to increase hit rate for semantically identical prompts.
        """
        normalized = " ".join(prompt.split())
        return f"{model}|{normalized}"

    def suggest_tool_creation(self, min_occurrences: int = 3) -> List[Dict[str, Any]]:
        """
        Return a list of suggestions where the same LLM call repeats across tasks.

        Each suggestion contains:
            - signature
            - occurrences
            - example_tasks (up to 3)
            - example_prompt (truncated)
        """
        suggestions = []
        with self._data_lock:
            for sig, count in self._prompt_signature_counter.items():
                if count >= min_occurrences:
                    examples = self._signature_to_examples[sig][:3]
                    example_tasks = [tid for tid, _ in examples]
                    example_prompt = sig.split("|", 1)[1]
                    suggestions.append(
                        {
                            "signature": sig,
                            "occurrences": count,
                            "example_tasks": example_tasks,
                            "example_prompt": (
                                example_prompt[:200] + "..."
                                if len(example_prompt) > 200
                                else example_prompt
                            ),
                        }
                    )
        return suggestions

    # --------------------------------------------------------------------- #
    # Persistence
    # --------------------------------------------------------------------- #
    def dump_snapshot(self, path: str) -> None:
        """Write a JSON snapshot of all collected metrics."""
        with self._data_lock:
            snapshot = {
                "llm_calls_per_task": self.llm_calls_per_task(),
                "tokens_per_task": self.tokens_per_task(),
                "tool_hits": self.tool_hits(),
                "tool_misses": self.tool_misses(),
                "component_assemblies": self.component_assemblies(),
                "full_builds": self.full_builds(),
                "failure_patterns": self.failure_patterns(),
                "cost_per_task": self.cost_per_task(),
                "tool_creation_suggestions": self.suggest_tool_creation(),
            }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, sort_keys=True)

    # --------------------------------------------------------------------- #
    # Convenience singleton accessor
    # --------------------------------------------------------------------- #
    @classmethod
    def get_instance(cls) -> "EfficiencyObserver":
        """Return the global observer instance."""
        return cls()


# Export a ready‑to‑use singleton for the rest of the codebase.
efficiency_observer = EfficiencyObserver.get_instance()