"""
efficiency_observer.py

Utility for observing and reporting efficiency metrics across Swarm tasks.
Tracks:
- LLM calls per task (model, prompt, token usage, cost)
- Tokens per task
- Tool hits / misses
- Component assemblies
- Full builds
- Failure patterns
- Cost per task

Provides a simple suggestion engine that flags repeated LLM calls
which could be wrapped into a reusable tool.
"""

from __future__ import annotations

import json
import threading
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional


@dataclass
class LLMCallRecord:
    model: str
    prompt: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    timestamp: float


@dataclass
class ToolUseRecord:
    tool_name: str
    hit: bool
    timestamp: float


@dataclass
class TaskMetrics:
    llm_calls: List[LLMCallRecord] = field(default_factory=list)
    tool_uses: List[ToolUseRecord] = field(default_factory=list)
    component_assemblies: List[str] = field(default_factory=list)
    full_build: bool = False
    failures: List[Tuple[str, str]] = field(default_factory=list)  # (exception_type, message)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def total_prompt_tokens(self) -> int:
        return sum(c.prompt_tokens for c in self.llm_calls)

    @property
    def total_completion_tokens(self) -> int:
        return sum(c.completion_tokens for c in self.llm_calls)

    @property
    def total_cost(self) -> float:
        return sum(c.cost for c in self.llm_calls)


class EfficiencyObserver:
    """
    Central observer for Swarm task efficiency.
    Thread‑safe; can be used from any part of the system.
    """

    _instance_lock = threading.Lock()
    _instance: Optional["EfficiencyObserver"] = None

    def __new__(cls, *args, **kwargs):
        # Singleton pattern – only one observer per process.
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super(EfficiencyObserver, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Guard against re‑initialisation in the singleton pattern
        if getattr(self, "_initialized", False):
            return
        self._tasks: Dict[str, TaskMetrics] = {}
        self._global_lock = threading.RLock()
        self._initialized = True

    # --------------------------------------------------------------------- #
    # Task lifecycle
    # --------------------------------------------------------------------- #
    def start_task(self, task_id: str, timestamp: float) -> None:
        with self._global_lock:
            if task_id in self._tasks:
                # Reset if re‑started
                self._tasks[task_id] = TaskMetrics(start_time=timestamp)
            else:
                self._tasks[task_id] = TaskMetrics(start_time=timestamp)

    def end_task(self, task_id: str, timestamp: float) -> None:
        with self._global_lock:
            if task_id in self._tasks:
                self._tasks[task_id].end_time = timestamp

    # --------------------------------------------------------------------- #
    # Recording primitives
    # --------------------------------------------------------------------- #
    def record_llm_call(
        self,
        task_id: str,
        model: str,
        prompt: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float,
        timestamp: float,
    ) -> None:
        record = LLMCallRecord(
            model=model,
            prompt=prompt,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            timestamp=timestamp,
        )
        with self._global_lock:
            self._tasks.setdefault(task_id, TaskMetrics()).llm_calls.append(record)

    def record_tool_use(self, task_id: str, tool_name: str, hit: bool, timestamp: float) -> None:
        record = ToolUseRecord(tool_name=tool_name, hit=hit, timestamp=timestamp)
        with self._global_lock:
            self._tasks.setdefault(task_id, TaskMetrics()).tool_uses.append(record)

    def record_component_assembly(self, task_id: str, component_name: str) -> None:
        with self._global_lock:
            self._tasks.setdefault(task_id, TaskMetrics()).component_assemblies.append(component_name)

    def record_full_build(self, task_id: str) -> None:
        with self._global_lock:
            self._tasks.setdefault(task_id, TaskMetrics()).full_build = True

    def record_failure(self, task_id: str, exc: BaseException) -> None:
        exc_type = type(exc).__name__
        message = str(exc)
        with self._global_lock:
            self._tasks.setdefault(task_id, TaskMetrics()).failures.append((exc_type, message))

    # --------------------------------------------------------------------- #
    # Aggregation helpers
    # --------------------------------------------------------------------- #
    def aggregate(self) -> Dict[str, Any]:
        """
        Returns a dictionary with aggregated statistics across all observed tasks.
        """
        with self._global_lock:
            agg = {
                "total_tasks": len(self._tasks),
                "llm_calls_per_task": {},
                "tokens_per_task": {},
                "cost_per_task": {},
                "tool_hits": Counter(),
                "tool_misses": Counter(),
                "component_assemblies": Counter(),
                "full_builds": 0,
                "failure_patterns": Counter(),
            }

            for task_id, metrics in self._tasks.items():
                agg["llm_calls_per_task"][task_id] = len(metrics.llm_calls)
                agg["tokens_per_task"][task_id] = {
                    "prompt": metrics.total_prompt_tokens,
                    "completion": metrics.total_completion_tokens,
                }
                agg["cost_per_task"][task_id] = metrics.total_cost

                # tool hits / misses
                for tu in metrics.tool_uses:
                    if tu.hit:
                        agg["tool_hits"][tu.tool_name] += 1
                    else:
                        agg["tool_misses"][tu.tool_name] += 1

                # component assemblies
                for comp in metrics.component_assemblies:
                    agg["component_assemblies"][comp] += 1

                # full builds
                if metrics.full_build:
                    agg["full_builds"] += 1

                # failures
                for exc_type, _ in metrics.failures:
                    agg["failure_patterns"][exc_type] += 1

            # Convert Counters to plain dicts for JSON friendliness
            agg["tool_hits"] = dict(agg["tool_hits"])
            agg["tool_misses"] = dict(agg["tool_misses"])
            agg["component_assemblies"] = dict(agg["component_assemblies"])
            agg["failure_patterns"] = dict(agg["failure_patterns"])

            return agg

    # --------------------------------------------------------------------- #
    # Suggestion engine
    # --------------------------------------------------------------------- #
    def suggest_tools(self, repeat_threshold: int = 3) -> List[Dict[str, Any]]:
        """
        Detects LLM call patterns that repeat across tasks and suggests
        creating a dedicated tool for them.

        Returns a list of suggestion dictionaries:
        {
            "model": "...",
            "prompt_signature": "...",  # truncated / hashed prompt
            "occurrences": N,
            "example_task_ids": [...]
        }
        """
        with self._global_lock:
            # Build a map: (model, prompt_signature) -> list of task_ids
            signature_map: Dict[Tuple[str, str], List[str]] = defaultdict(list)

            for task_id, metrics in self._tasks.items():
                for call in metrics.llm_calls:
                    # Simple signature: first 120 chars stripped of whitespace
                    sig = " ".join(call.prompt.split())[:120]
                    signature_map[(call.model, sig)].append(task_id)

            suggestions = []
            for (model, sig), task_ids in signature_map.items():
                if len(task_ids) >= repeat_threshold:
                    suggestions.append(
                        {
                            "model": model,
                            "prompt_signature": sig,
                            "occurrences": len(task_ids),
                            "example_task_ids": task_ids[:5],
                        }
                    )
            return suggestions

    # --------------------------------------------------------------------- #
    # Reporting utilities
    # --------------------------------------------------------------------- #
    def dump_to_json(self, file_path: str) -> None:
        """
        Serialises the full observation data (per‑task) to a JSON file.
        """
        with self._global_lock:
            serialisable = {
                task_id: {
                    "llm_calls": [
                        {
                            "model": c.model,
                            "prompt": c.prompt,
                            "prompt_tokens": c.prompt_tokens,
                            "completion_tokens": c.completion_tokens,
                            "cost": c.cost,
                            "timestamp": c.timestamp,
                        }
                        for c in metrics.llm_calls
                    ],
                    "tool_uses": [
                        {"tool_name": t.tool_name, "hit": t.hit, "timestamp": t.timestamp}
                        for t in metrics.tool_uses
                    ],
                    "component_assemblies": metrics.component_assemblies,
                    "full_build": metrics.full_build,
                    "failures": [{"type": ft, "message": msg} for ft, msg in metrics.failures],
                    "start_time": metrics.start_time,
                    "end_time": metrics.end_time,
                }
                for task_id, metrics in self._tasks.items()
            }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, indent=2, ensure_ascii=False)

    def __repr__(self) -> str:
        agg = self.aggregate()
        return f"<EfficiencyObserver tasks={agg['total_tasks']} full_builds={agg['full_builds']}>"

# Convenience singleton accessor
def get_observer() -> EfficiencyObserver:
    return EfficiencyObserver()