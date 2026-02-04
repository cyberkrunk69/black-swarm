"""
efficiency_observer.py

Utility for observing and reporting efficiency metrics of the Swarm architecture.
Tracks per‑task statistics such as:
- LLM calls (count & model)
- Token usage
- Tool hit / miss ratios
- Component assemblies
- Full builds
- Failure patterns
- Estimated cost per task

When repetitive LLM calls are detected, the observer can suggest creating a
dedicated tool to encapsulate the repeated logic.

The observer is deliberately lightweight and does not depend on any external
services; it only records data in‑memory and can dump a JSON report on demand.
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional


# --------------------------------------------------------------------------- #
# Helper dataclasses
# --------------------------------------------------------------------------- #

@dataclass
class LLMCallRecord:
    model: str
    prompt: str
    response: str
    prompt_tokens: int
    response_tokens: int
    duration: float
    timestamp: float = field(default_factory=time.time)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.response_tokens

    @property
    def cost(self) -> float:
        """Very rough cost estimation (USD). Adjust rates as needed."""
        # Example rates (USD per 1k tokens)
        rates = {
            "gpt-4": 0.03,
            "gpt-3.5-turbo": 0.002,
        }
        rate = rates.get(self.model, 0.005)  # fallback default
        return (self.total_tokens / 1000) * rate


@dataclass
class ToolUsageRecord:
    tool_name: str
    hit: bool
    timestamp: float = field(default_factory=time.time)


@dataclass
class ComponentAssemblyRecord:
    component_name: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class BuildRecord:
    success: bool
    failure_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


# --------------------------------------------------------------------------- #
# Core observer
# --------------------------------------------------------------------------- #

class EfficiencyObserver:
    """
    Singleton‑style observer that aggregates metrics across tasks.
    All methods are thread‑safe.
    """

    _instance: Optional["EfficiencyObserver"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EfficiencyObserver":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_internal()
            return cls._instance

    # ------------------------------------------------------------------- #
    # Internal state initialisation
    # ------------------------------------------------------------------- #

    def _init_internal(self) -> None:
        self.task_start_times: Dict[str, float] = {}
        self.llm_calls: Dict[str, List[LLMCallRecord]] = defaultdict(list)
        self.tool_usages: Dict[str, List[ToolUsageRecord]] = defaultdict(list)
        self.component_assemblies: Dict[str, List[ComponentAssemblyRecord]] = defaultdict(list)
        self.builds: Dict[str, List[BuildRecord]] = defaultdict(list)

        # Aggregated counters for quick look‑ups
        self.llm_call_counter: Counter[Tuple[str, str]] = Counter()  # (model, prompt_hash)
        self.tool_hit_counter: Counter[str] = Counter()
        self.tool_miss_counter: Counter[str] = Counter()
        self.failure_patterns: Counter[str] = Counter()

        self._data_lock = threading.RLock()

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    # ----- Task lifecycle ------------------------------------------------ #
    def start_task(self, task_id: str) -> None:
        """Mark the beginning of a new task."""
        with self._data_lock:
            self.task_start_times[task_id] = time.time()

    def end_task(self, task_id: str) -> None:
        """Mark the end of a task. No side‑effects other than cleanup."""
        with self._data_lock:
            self.task_start_times.pop(task_id, None)

    # ----- LLM call tracking --------------------------------------------- #
    def record_llm_call(
        self,
        task_id: str,
        model: str,
        prompt: str,
        response: str,
        prompt_tokens: int,
        response_tokens: int,
        duration: float,
    ) -> None:
        """Record an LLM interaction for a given task."""
        record = LLMCallRecord(
            model=model,
            prompt=prompt,
            response=response,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            duration=duration,
        )
        prompt_hash = self._hash_prompt(prompt)

        with self._data_lock:
            self.llm_calls[task_id].append(record)
            self.llm_call_counter[(model, prompt_hash)] += 1

    # ----- Tool usage tracking ------------------------------------------- #
    def record_tool_usage(self, task_id: str, tool_name: str, hit: bool) -> None:
        """Record whether a tool was successfully used (hit) or not (miss)."""
        rec = ToolUsageRecord(tool_name=tool_name, hit=hit)
        with self._data_lock:
            self.tool_usages[task_id].append(rec)
            if hit:
                self.tool_hit_counter[tool_name] += 1
            else:
                self.tool_miss_counter[tool_name] += 1

    # ----- Component assembly tracking ------------------------------------ #
    def record_component_assembly(self, task_id: str, component_name: str) -> None:
        rec = ComponentAssemblyRecord(component_name=component_name)
        with self._data_lock:
            self.component_assemblies[task_id].append(rec)

    # ----- Build tracking ------------------------------------------------ #
    def record_build(self, task_id: str, success: bool, failure_reason: Optional[str] = None) -> None:
        rec = BuildRecord(success=success, failure_reason=failure_reason)
        with self._data_lock:
            self.builds[task_id].append(rec)
            if not success and failure_reason:
                self.failure_patterns[failure_reason] += 1

    # ----- Reporting ------------------------------------------------------ #
    def generate_report(self) -> Dict[str, Any]:
        """Return a dict with aggregated statistics."""
        with self._data_lock:
            total_tasks = len(set(self.llm_calls.keys()) |
                              set(self.tool_usages.keys()) |
                              set(self.component_assemblies.keys()) |
                              set(self.builds.keys()))

            # LLM stats
            llm_stats = {}
            for (model, prompt_hash), cnt in self.llm_call_counter.items():
                llm_stats.setdefault(model, []).append(
                    {"prompt_hash": prompt_hash, "calls": cnt}
                )

            # Tool hit/miss
            tool_stats = {}
            for tool in set(self.tool_hit_counter) | set(self.tool_miss_counter):
                hits = self.tool_hit_counter.get(tool, 0)
                misses = self.tool_miss_counter.get(tool, 0)
                total = hits + misses
                tool_stats[tool] = {
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": hits / total if total else None,
                }

            # Cost per task
            cost_per_task = {}
            for task_id, calls in self.llm_calls.items():
                cost_per_task[task_id] = sum(c.cost for c in calls)

            # Assemble final report
            report = {
                "total_tasks": total_tasks,
                "llm_calls_per_task": {tid: len(calls) for tid, calls in self.llm_calls.items()},
                "tokens_per_task": {
                    tid: sum(c.total_tokens for c in calls) for tid, calls in self.llm_calls.items()
                },
                "tool_stats": tool_stats,
                "component_assemblies_per_task": {
                    tid: len(assemblies) for tid, assemblies in self.component_assemblies.items()
                },
                "full_builds_per_task": {
                    tid: sum(1 for b in builds if b.success) for tid, builds in self.builds.items()
                },
                "failure_patterns": dict(self.failure_patterns),
                "cost_per_task": cost_per_task,
                "suggested_tools": self._suggest_tools(),
            }
            return report

    def dump_report(self, path: str) -> None:
        """Write the JSON report to the supplied filesystem path."""
        report = self.generate_report()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)

    # ----- Suggestion engine --------------------------------------------- #
    def _suggest_tools(self, repeat_threshold: int = 5) -> List[Dict[str, Any]]:
        """
        Identify LLM call patterns that repeat often enough to merit a dedicated tool.

        Returns a list of suggestion dicts:
            {
                "model": "...",
                "prompt_hash": "...",
                "repeat_count": N,
                "suggestion": "Create a tool encapsulating this call."
            }
        """
        suggestions = []
        for (model, prompt_hash), cnt in self.llm_call_counter.items():
            if cnt >= repeat_threshold:
                suggestions.append(
                    {
                        "model": model,
                        "prompt_hash": prompt_hash,
                        "repeat_count": cnt,
                        "suggestion": "Consider implementing a custom tool for this repeated LLM call.",
                    }
                )
        return suggestions

    # ------------------------------------------------------------------- #
    # Utility helpers
    # ------------------------------------------------------------------- #

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """Create a deterministic short hash for a prompt string."""
        import hashlib

        h = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return h[:12]  # truncate for readability


# --------------------------------------------------------------------------- #
# Convenience singleton accessor
# --------------------------------------------------------------------------- #

def get_observer() -> EfficiencyObserver:
    """Return the global EfficiencyObserver instance."""
    return EfficiencyObserver()


# --------------------------------------------------------------------------- #
# Example usage (removed in production; kept as docstring)
# --------------------------------------------------------------------------- #
"""
# In any task:
obs = get_observer()
obs.start_task(task_id)

# After an LLM call:
obs.record_llm_call(
    task_id=task_id,
    model="gpt-4",
    prompt=user_prompt,
    response=llm_reply,
    prompt_tokens=120,
    response_tokens=350,
    duration=0.73,
)

# Tool usage:
obs.record_tool_usage(task_id, tool_name="search_api", hit=True)

# Component assembly:
obs.record_component_assembly(task_id, component_name="UserProfileBuilder")

# Build result:
obs.record_build(task_id, success=False, failure_reason="TimeoutError")

# At the end:
obs.end_task(task_id)

# Dump report:
obs.dump_report("/tmp/efficiency_report.json")
"""