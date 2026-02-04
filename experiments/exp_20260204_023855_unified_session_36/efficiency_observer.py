\"\"\"efficiency_observer.py

Utility for observing and analysing efficiency metrics across tasks in a SWARM
architecture.  The observer records:

* LLM calls per task (including model name, prompt hash and token usage)
* Tokens consumed per task
* Tool hit / miss statistics
* Component assembly counts
* Full‑build counts
* Failure patterns (exception types, messages, task ids)
* Cost per task (derived from token usage & model pricing)

It also provides a simple recommendation engine that suggests creating a
dedicated tool when the same LLM call (identical prompt & model) repeats
multiple times across tasks.

The observer is deliberately lightweight – it stores data in‑memory and can be
periodically flushed to a JSON file if required.  It is safe for use from
multiple threads via ``threading.Lock``.
\"\"\"

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def _hash_prompt(prompt: str) -> str:
    \"\"\"Return a deterministic short hash for a prompt string.\n\n    The hash is used to identify identical LLM calls across tasks.\n    \"\"\"
    return hashlib.sha256(prompt.encode(\"utf-8\")).hexdigest()[:12]


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class LLMCallRecord:
    model: str
    prompt_hash: str
    prompt: str
    tokens_used: int
    cost_usd: float
    task_id: str


@dataclass
class ToolUsageRecord:
    tool_name: str
    hit: bool
    task_id: str


@dataclass
class FailureRecord:
    exception_type: str
    message: str
    task_id: str


# --------------------------------------------------------------------------- #
# Core observer class
# --------------------------------------------------------------------------- #
class EfficiencyObserver:
    \"\"\"Collects runtime efficiency metrics for a SWARM session.\n\n    Typical usage pattern::\n\n        observer = EfficiencyObserver()\n        # inside a task\n        observer.record_llm_call(\n            task_id=task.id,\n            model=\"gpt-4\",\n            prompt=prompt,\n            tokens_used=token_cnt,\n            cost_usd=0.03,\n        )\n        observer.record_tool_use(task_id=task.id, tool_name=\"search\", hit=True)\n        # on failure\n        observer.record_failure(task_id=task.id, exc=exc)\n        # after the run you can ask for suggestions\n        suggestions = observer.suggest_tools()\n    \"\"\"\n\n    # --------------------------------------------------------------------- #
    # Construction / persistence
    # --------------------------------------------------------------------- #
    def __init__(self, persist_path: str | Path | None = None) -> None:\n        self._lock = threading.Lock()\n        # Raw records\n        self.llm_calls: List[LLMCallRecord] = []\n        self.tool_usages: List[ToolUsageRecord] = []\n        self.failures: List[FailureRecord] = []\n        self.component_assemblies: Counter[str] = Counter()\n        self.full_builds: Counter[str] = Counter()\n        # Aggregated counters (computed lazily for speed)\n        self._llm_calls_per_task: Counter[str] = Counter()\n        self._tokens_per_task: Counter[str] = Counter()\n        self._cost_per_task: Counter[str] = Counter()\n        self._tool_hits: Counter[str] = Counter()\n        self._tool_misses: Counter[str] = Counter()\n        # Optional persistence location\n        self.persist_path = Path(persist_path) if persist_path else None\n\n    # --------------------------------------------------------------------- #
    # Recording API
    # --------------------------------------------------------------------- #
    def record_llm_call(\n        self,\n        *,\n        task_id: str,\n        model: str,\n        prompt: str,\n        tokens_used: int,\n        cost_usd: float,\n    ) -> None:\n        \"\"\"Record a single LLM invocation.\n\n        Parameters\n        ----------\n        task_id: str\n            Identifier of the task that performed the call.\n        model: str\n            Model name (e.g. ``gpt-4``).\n        prompt: str\n            The exact prompt sent to the model.\n        tokens_used: int\n            Number of tokens consumed (prompt + completion).\n        cost_usd: float\n            Cost incurred for this call.\n        \"\"\"\n        prompt_hash = _hash_prompt(prompt)\n        record = LLMCallRecord(\n            model=model,\n            prompt_hash=prompt_hash,\n            prompt=prompt,\n            tokens_used=tokens_used,\n            cost_usd=cost_usd,\n            task_id=task_id,\n        )\n        with self._lock:\n            self.llm_calls.append(record)\n            self._llm_calls_per_task[task_id] += 1\n            self._tokens_per_task[task_id] += tokens_used\n            self._cost_per_task[task_id] += cost_usd\n        logger.debug(\n            \"LLM call recorded: task=%s model=%s tokens=%d cost=%.4f\",\n            task_id,\n            model,\n            tokens_used,\n            cost_usd,\n        )\n\n    def record_tool_use(self, *, task_id: str, tool_name: str, hit: bool) -> None:\n        \"\"\"Record a tool usage attempt.\n\n        ``hit`` indicates whether the tool produced a useful result.\n        \"\"\"\n        rec = ToolUsageRecord(tool_name=tool_name, hit=hit, task_id=task_id)\n        with self._lock:\n            self.tool_usages.append(rec)\n            if hit:\n                self._tool_hits[tool_name] += 1\n            else:\n                self._tool_misses[tool_name] += 1\n        logger.debug(\n            \"Tool usage recorded: task=%s tool=%s hit=%s\", task_id, tool_name, hit\n        )\n\n    def record_component_assembly(self, component_name: str) -> None:\n        \"\"\"Increment the count of a component being assembled.\n\n        This is useful for tracking how many times a particular reusable\n        component (e.g. a sub‑workflow) is constructed.\n        \"\"\"\n        with self._lock:\n            self.component_assemblies[component_name] += 1\n        logger.debug(\"Component assembled: %s\", component_name)\n\n    def record_full_build(self, build_name: str) -> None:\n        \"\"\"Record a complete system build (e.g., a final assembly).\n        \"\"\"\n        with self._lock:\n            self.full_builds[build_name] += 1\n        logger.debug(\"Full build recorded: %s\", build_name)\n\n    def record_failure(self, *, task_id: str, exc: BaseException) -> None:\n        \"\"\"Record a failure occurring within a task.\n        \"\"\"\n        rec = FailureRecord(\n            exception_type=type(exc).__name__, message=str(exc), task_id=task_id\n        )\n        with self._lock:\n            self.failures.append(rec)\n        logger.warning(\n            \"Task %s failed with %s: %s\", task_id, rec.exception_type, rec.message\n        )\n\n    # --------------------------------------------------------------------- #
    # Aggregation helpers (read‑only properties)\n    # --------------------------------------------------------------------- #
    @property\n    def llm_calls_per_task(self) -> Dict[str, int]:\n        return dict(self._llm_calls_per_task)\n\n    @property\n    def tokens_per_task(self) -> Dict[str, int]:\n        return dict(self._tokens_per_task)\n\n    @property\n    def cost_per_task(self) -> Dict[str, float]:\n        return dict(self._cost_per_task)\n\n    @property\n    def tool_hit_rate(self) -> Dict[str, float]:\n        with self._lock:\n            rates: Dict[str, float] = {}\n            for tool, hits in self._tool_hits.items():\n                misses = self._tool_misses.get(tool, 0)\n                total = hits + misses\n                rates[tool] = hits / total if total else 0.0\n            return rates\n\n    @property\n    def failure_patterns(self) -> Counter[Tuple[str, str]]:\n        \"\"\"Return a Counter keyed by (exception_type, message).\n        \"\"\"\n        with self._lock:\n            return Counter((f.exception_type, f.message) for f in self.failures)\n\n    # --------------------------------------------------------------------- #
    # Recommendation engine\n    # --------------------------------------------------------------------- #
    def suggest_tools(self, repeat_threshold: int = 3) -> List[Dict[str, Any]]:\n        \"\"\"Suggest new tools based on repeated identical LLM calls.\n\n        Parameters\n        ----------\n        repeat_threshold: int, default 3\n            Minimum number of identical calls (same model + prompt hash) before a\n            suggestion is emitted.\n\n        Returns\n        -------\n        List[Dict]\n            Each dict contains ``model``, ``prompt_hash``, ``example_prompt``\n            and ``occurrences``.\n        \"\"\"\n        with self._lock:\n            # Group calls by (model, prompt_hash)\n            grouping: Counter[Tuple[str, str]] = Counter()\n            example_prompt: Dict[Tuple[str, str], str] = {}\n            for rec in self.llm_calls:\n                key = (rec.model, rec.prompt_hash)\n                grouping[key] += 1\n                # Keep the first seen prompt as an example\n                if key not in example_prompt:\n                    example_prompt[key] = rec.prompt\n\n            suggestions = []\n            for (model, phash), count in grouping.items():\n                if count >= repeat_threshold:\n                    suggestions.append(\n                        {\n                            \"model\": model,\n                            \"prompt_hash\": phash,\n                            \"example_prompt\": example_prompt[(model, phash)],\n                            \"occurrences\": count,\n                        }\n                    )\n            return suggestions\n\n    # --------------------------------------------------------------------- #
    # Persistence helpers (optional)\n    # --------------------------------------------------------------------- #
    def dump_to_json(self, path: str | Path | None = None) -> Path:\n        \"\"\"Serialise the collected metrics to a JSON file.\n\n        If *path* is omitted the ``persist_path`` supplied at construction time\n        is used.  The method returns the absolute path of the written file.\n        \"\"\"\n        target = Path(path) if path else self.persist_path\n        if not target:\n            raise ValueError(\"No persistence path supplied for dump_to_json\")\n\n        data = {\n            \"llm_calls\": [rec.__dict__ for rec in self.llm_calls],\n            \"tool_usages\": [rec.__dict__ for rec in self.tool_usages],\n            \"failures\": [rec.__dict__ for rec in self.failures],\n            \"component_assemblies\": dict(self.component_assemblies),\n            \"full_builds\": dict(self.full_builds),\n            \"aggregates\": {\n                \"llm_calls_per_task\": dict(self._llm_calls_per_task),\n                \"tokens_per_task\": dict(self._tokens_per_task),\n                \"cost_per_task\": dict(self._cost_per_task),\n                \"tool_hits\": dict(self._tool_hits),\n                \"tool_misses\": dict(self._tool_misses),\n            },\n        }\n        target.parent.mkdir(parents=True, exist_ok=True)\n        with target.open(\"w\", encoding=\"utf-8\") as f:\n            json.dump(data, f, indent=2, ensure_ascii=False)\n        logger.info(\"EfficiencyObserver data dumped to %s\", target)\n        return target.resolve()\n\n    def load_from_json(self, path: str | Path) -> None:\n        \"\"\"Load previously persisted metrics.\n\n        The current in‑memory state is cleared before loading.\n        \"\"\"\n        src = Path(path)\n        if not src.is_file():\n            raise FileNotFoundError(f\"{src} does not exist\")\n        with src.open(\"r\", encoding=\"utf-8\") as f:\n            data = json.load(f)\n\n        with self._lock:\n            self.llm_calls = [LLMCallRecord(**d) for d in data.get(\"llm_calls\", [])]\n            self.tool_usages = [ToolUsageRecord(**d) for d in data.get(\"tool_usages\", [])]\n            self.failures = [FailureRecord(**d) for d in data.get(\"failures\", [])]\n            self.component_assemblies = Counter(data.get(\"component_assemblies\", {}))\n            self.full_builds = Counter(data.get(\"full_builds\", {}))\n            # Re‑build aggregates\n            self._llm_calls_per_task = Counter(data[\"aggregates\"].get(\"llm_calls_per_task\", {}))\n            self._tokens_per_task = Counter(data[\"aggregates\"].get(\"tokens_per_task\", {}))\n            self._cost_per_task = Counter(data[\"aggregates\"].get(\"cost_per_task\", {}))\n            self._tool_hits = Counter(data[\"aggregates\"].get(\"tool_hits\", {}))\n            self._tool_misses = Counter(data[\"aggregates\"].get(\"tool_misses\", {}))\n        logger.info(\"EfficiencyObserver state restored from %s\", src)\n\n    # --------------------------------------------------------------------- #
    # Human‑readable summary\n    # --------------------------------------------------------------------- #
    def summary(self) -> str:\n        \"\"\"Return a concise multi‑line string summarising the collected data.\"\"\"\n        lines = []\n        lines.append(\"=== Efficiency Observer Summary ===\")\n        lines.append(f\"Total LLM calls: {len(self.llm_calls)}\")\n        lines.append(f\"Total tokens consumed: {sum(self._tokens_per_task.values())}\")\n        lines.append(f\"Total cost (USD): ${sum(self._cost_per_task.values()):.4f}\")\n        lines.append(f\"Tool hit rate: {json.dumps(self.tool_hit_rate, indent=2)}\")\n        lines.append(f\"Component assemblies: {dict(self.component_assemblies)}\")\n        lines.append(f\"Full builds: {dict(self.full_builds)}\")\n        lines.append(f\"Failure patterns: {self.failure_patterns.most_common(5)}\")\n        suggestions = self.suggest_tools()\n        if suggestions:\n            lines.append(\"Potential tool creation suggestions (repeated LLM calls):\")\n            for s in suggestions:\n                lines.append(\n                    f\" - Model {s['model']} | Prompt hash {s['prompt_hash']} | Occurrences {s['occurrences']}\"\n                )\n        else:\n            lines.append(\"No tool creation suggestions detected.\")\n        return \"\\n\".join(lines)\n\n# End of file\n