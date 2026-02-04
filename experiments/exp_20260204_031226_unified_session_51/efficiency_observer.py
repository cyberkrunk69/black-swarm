\"\"\"efficiency_observer.py

Utility for observing and reporting efficiency metrics across SWARM tasks.

The observer tracks:
* LLM calls per task (count & model usage)
* Token usage per task
* Cost per task
* Tool hit / miss statistics
* Component assembly counts
* Full build occurrences
* Failure patterns

It also provides a simple heuristic to suggest creation of a reusable tool when the
same LLM call (model + prompt signature) repeats across multiple tasks.
\"\"\"

from __future__ import annotations

import collections
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, DefaultDict, Any

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #


@dataclass
class LLMCallRecord:
    model: str
    prompt_signature: str  # a short hash / identifier of the prompt template
    tokens: int
    cost: float
    timestamp: float = field(default_factory=lambda: threading.get_ident())  # placeholder


@dataclass
class TaskMetrics:
    llm_calls: List[LLMCallRecord] = field(default_factory=list)
    tool_hits: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
    tool_misses: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
    component_assemblies: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))
    full_builds: int = 0
    failures: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))


class EfficiencyObserver:
    \"\"\"Collects runtime efficiency data for SWARM tasks.

    The observer is thread‑safe and can be instantiated once per experiment.
    \"\"\"

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tasks: DefaultDict[str, TaskMetrics] = collections.defaultdict(TaskMetrics)

        # Global aggregates used for suggestions
        self._global_llm_signature_counts: DefaultDict[Tuple[str, str], int] = collections.defaultdict(int)

    # --------------------------------------------------------------------- #
    # Recording helpers
    # --------------------------------------------------------------------- #

    def record_llm_call(
        self,
        task_id: str,
        model: str,
        prompt_signature: str,
        tokens: int,
        cost: float,
    ) -> None:
        \"\"\"Record an LLM invocation for a given task.

        Args:
            task_id: Unique identifier of the task.
            model: Name of the model used (e.g., ``gpt-4``).
            prompt_signature: Short identifier of the prompt (hash or description).
            tokens: Number of tokens consumed.
            cost: Monetary cost of the call.
        \"\"\"
        with self._lock:
            record = LLMCallRecord(model=model, prompt_signature=prompt_signature, tokens=tokens, cost=cost)
            self._tasks[task_id].llm_calls.append(record)
            self._global_llm_signature_counts[(model, prompt_signature)] += 1
            log.debug(
                \"LLM call recorded – task=%s model=%s signature=%s tokens=%s cost=%s\",
                task_id,
                model,
                prompt_signature,
                tokens,
                cost,
            )

    def record_tool_use(self, task_id: str, tool_name: str, hit: bool = True) -> None:
        \"\"\"Record a tool lookup result.

        Args:
            task_id: Unique identifier of the task.
            tool_name: Name of the tool queried.
            hit: ``True`` if the tool was found and used, ``False`` otherwise.
        \"\"\"
        with self._lock:
            if hit:
                self._tasks[task_id].tool_hits[tool_name] += 1
            else:
                self._tasks[task_id].tool_misses[tool_name] += 1
            log.debug(
                \"Tool %s recorded – task=%s hit=%s\", tool_name, task_id, hit
            )

    def record_component_assembly(self, task_id: str, component_name: str) -> None:
        \"\"\"Record that a component was assembled during a task.\"\"\"
        with self._lock:
            self._tasks[task_id].component_assemblies[component_name] += 1
            log.debug(
                \"Component assembly recorded – task=%s component=%s\", task_id, component_name
            )

    def record_full_build(self, task_id: str) -> None:
        \"\"\"Increment the full‑build counter for the given task.\"\"\"
        with self._lock:
            self._tasks[task_id].full_builds += 1
            log.debug(\"Full build recorded – task=%s\", task_id)

    def record_failure(self, task_id: str, pattern: str) -> None:
        \"\"\"Record a failure pattern observed in a task.\n\n        Args:\n            task_id: Unique identifier of the task.\n            pattern: Short description or identifier of the failure.\n        \"\"\"\n        with self._lock:\n            self._tasks[task_id].failures[pattern] += 1\n            log.debug(\"Failure recorded – task=%s pattern=%s\", task_id, pattern)

    # --------------------------------------------------------------------- #
    # Aggregation helpers
    # --------------------------------------------------------------------- #

    def _aggregate_task(self, task_id: str) -> Dict[str, Any]:
        \"\"\"Return a flat dictionary of aggregated metrics for a single task.\"\"\"
        metrics = self._tasks[task_id]
        llm_calls = len(metrics.llm_calls)
        tokens = sum(c.tokens for c in metrics.llm_calls)
        cost = sum(c.cost for c in metrics.llm_calls)

        return {
            \"llm_calls\": llm_calls,
            \"tokens\": tokens,
            \"cost\": cost,
            \"tool_hits\": dict(metrics.tool_hits),
            \"tool_misses\": dict(metrics.tool_misses),
            \"component_assemblies\": dict(metrics.component_assemblies),
            \"full_builds\": metrics.full_builds,
            \"failures\": dict(metrics.failures),
        }

    def get_task_summary(self, task_id: str) -> Dict[str, Any]:
        \"\"\"Public accessor for a task's aggregated metrics.\"\"\"
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f\"Task ID {task_id!r} not found in observer.\")
            return self._aggregate_task(task_id)

    def get_overall_summary(self) -> Dict[str, Any]:
        \"\"\"Return aggregated metrics across *all* observed tasks.\"\"\"
        with self._lock:
            total = {
                \"llm_calls\": 0,
                \"tokens\": 0,
                \"cost\": 0.0,
                \"tool_hits\": collections.defaultdict(int),
                \"tool_misses\": collections.defaultdict(int),
                \"component_assemblies\": collections.defaultdict(int),
                \"full_builds\": 0,
                \"failures\": collections.defaultdict(int),
            }

            for task_id in self._tasks:
                agg = self._aggregate_task(task_id)
                total[\"llm_calls\"] += agg[\"llm_calls\"]
                total[\"tokens\"] += agg[\"tokens\"]
                total[\"cost\"] += agg[\"cost\"]
                total[\"full_builds\"] += agg[\"full_builds\"]
                for k, v in agg[\"tool_hits\"].items():
                    total[\"tool_hits\"][k] += v
                for k, v in agg[\"tool_misses\"].items():
                    total[\"tool_misses\"][k] += v
                for k, v in agg[\"component_assemblies\"].items():
                    total[\"component_assemblies\"][k] += v
                for k, v in agg[\"failures\"].items():
                    total[\"failures\"][k] += v

            # Convert defaultdicts to plain dicts for JSON friendliness
            total[\"tool_hits\"] = dict(total[\"tool_hits\"])
            total[\"tool_misses\"] = dict(total[\"tool_misses\"])
            total[\"component_assemblies\"] = dict(total[\"component_assemblies\"])
            total[\"failures\"] = dict(total[\"failures\"])

            return total

    # --------------------------------------------------------------------- #
    # Suggestion engine
    # --------------------------------------------------------------------- #

    def suggest_tool_creation(self, repeat_threshold: int = 3) -> List[Dict[str, Any]]:
        \"\"\"Suggest new tool abstractions based on repeated LLM calls.

        The heuristic looks for (model, prompt_signature) pairs that have been
        observed at least *repeat_threshold* times across *any* tasks.  When such a
        pattern is found, a suggestion dictionary is returned.

        Returns:
            List of suggestion dictionaries, each containing:
                * ``model`` – the LLM model used.
                * ``prompt_signature`` – identifier of the repeated prompt.
                * ``occurrences`` – how many times the pattern was seen.
                * ``example_task_ids`` – up to three task IDs where it occurred.
        \"\"\"
        with self._lock:
            suggestions: List[Dict[str, Any]] = []

            # Build reverse index: signature -> set(task_id)
            signature_to_tasks: DefaultDict[Tuple[str, str], set] = collections.defaultdict(set)
            for task_id, metrics in self._tasks.items():
                for call in metrics.llm_calls:
                    signature_to_tasks[(call.model, call.prompt_signature)].add(task_id)

            for (model, signature), task_set in signature_to_tasks.items():
                occ = len(task_set)
                if occ >= repeat_threshold:
                    suggestions.append(
                        {
                            \"model\": model,
                            \"prompt_signature\": signature,
                            \"occurrences\": occ,
                            \"example_task_ids\": list(task_set)[:3],
                        }
                    )

            return suggestions

    # --------------------------------------------------------------------- #
    # Persistence helpers (optional)
    # --------------------------------------------------------------------- #

    def dump_to_json(self, file_path: str) -> None:
        \"\"\"Serialize the full observer state to a JSON file.\n\n        The JSON structure mirrors the output of ``get_overall_summary`` and\n        includes the raw LLM call records for deeper inspection.\n        \"\"\"
        with self._lock, open(file_path, \"w\", encoding=\"utf-8\") as f:
            data = {
                \"tasks\": {
                    task_id: {
                        \"llm_calls\": [
                            {
                                \"model\": c.model,
                                \"prompt_signature\": c.prompt_signature,
                                \"tokens\": c.tokens,
                                \"cost\": c.cost,
                                \"timestamp\": c.timestamp,
                            }
                            for c in metrics.llm_calls
                        ],
                        \"tool_hits\": dict(metrics.tool_hits),
                        \"tool_misses\": dict(metrics.tool_misses),
                        \"component_assemblies\": dict(metrics.component_assemblies),
                        \"full_builds\": metrics.full_builds,
                        \"failures\": dict(metrics.failures),
                    }
                    for task_id, metrics in self._tasks.items()
                }
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
            log.info(\"EfficiencyObserver state dumped to %s\", file_path)

    def load_from_json(self, file_path: str) -> None:
        \"\"\"Load a previously saved observer state.\n\n        This method overwrites any existing in‑memory data.\n        \"\"\"
        with self._lock, open(file_path, \"r\", encoding=\"utf-8\") as f:
            data = json.load(f)

        self._tasks.clear()
        self._global_llm_signature_counts.clear()

        for task_id, payload in data.get(\"tasks\", {}).items():
            metrics = TaskMetrics()
            for call in payload.get(\"llm_calls\", []):
                record = LLMCallRecord(
                    model=call[\"model\"],
                    prompt_signature=call[\"prompt_signature\"],
                    tokens=call[\"tokens\"],
                    cost=call[\"cost\"],
                    timestamp=call.get(\"timestamp\", 0.0),
                )
                metrics.llm_calls.append(record)
                self._global_llm_signature_counts[(record.model, record.prompt_signature)] += 1

            metrics.tool_hits.update(payload.get(\"tool_hits\", {}))
            metrics.tool_misses.update(payload.get(\"tool_misses\", {}))
            metrics.component_assemblies.update(payload.get(\"component_assemblies\", {}))
            metrics.full_builds = payload.get(\"full_builds\", 0)
            metrics.failures.update(payload.get(\"failures\", {}))

            self._tasks[task_id] = metrics

        log.info(\"EfficiencyObserver state loaded from %s\", file_path)


# --------------------------------------------------------------------------- #
# Convenience singleton (optional – can be imported directly)
# --------------------------------------------------------------------------- #

default_observer = EfficiencyObserver()

__all__ = [
    \"EfficiencyObserver\",
    \"default_observer\",
]