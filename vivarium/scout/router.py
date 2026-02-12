"""
Scout router — orchestrates triggers, respects limits, prevents infinite loops,
and cascades doc updates safely.

The traffic cop: decides what gets in, when to spend, and when to escalate.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from vivarium.scout.audit import AuditLog
from vivarium.scout.config import ScoutConfig, HARD_MAX_HOURLY_BUDGET
from vivarium.scout.ignore import IgnorePatterns
from vivarium.scout.validator import ValidationResult, Validator, validate_location


# Token cost estimates (8B: $0.20/million, 70B: ~$0.90/million)
TOKENS_PER_SMALL_FILE = 500
COST_PER_MILLION_8B = 0.20
COST_PER_MILLION_70B = 0.90
BRIEF_COST_PER_FILE = 0.005
TASK_NAV_ESTIMATED_COST = 0.002  # 8B + retry + possible 70B escalation


@dataclass
class NavResult:
    """Result of scout-nav LLM call."""

    suggestion: dict
    cost: float
    duration_ms: int
    signature_changed: bool = False
    new_exports: bool = False


@dataclass
class SymbolDoc:
    """Generated symbol documentation."""

    content: str
    generation_cost: float


def _notify_user(message: str) -> None:
    """Notify user (stub — override for testing or real UI)."""
    # Could use logging, print, or IDE notification
    import logging

    logging.getLogger(__name__).info("Scout: %s", message)


class TriggerRouter:
    """
    Orchestrates triggers, respects limits, prevents infinite loops,
    and cascades doc updates safely.
    """

    def __init__(
        self,
        config: ScoutConfig = None,
        audit: AuditLog = None,
        validator: Validator = None,
        repo_root: Path = None,
        notify: Callable[[str], None] = None,
    ):
        self.config = config or ScoutConfig()
        self.audit = audit or AuditLog()
        self.validator = validator or Validator()
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.notify = notify or _notify_user
        self.ignore = IgnorePatterns(repo_root=self.repo_root)

    def should_trigger(self, files: List[Path]) -> List[Path]:
        """Filter ignored files, return relevant subset."""
        return [f for f in files if not self.ignore.matches(f, self.repo_root)]

    def _quick_token_estimate(self, path: Path) -> int:
        """Quick symbol/code size estimate for cost prediction."""
        try:
            if not path.exists():
                return TOKENS_PER_SMALL_FILE
            content = path.read_text(encoding="utf-8", errors="replace")
            # Rough: ~4 chars per token for code
            return max(100, min(len(content) // 4, 5000))
        except OSError:
            return TOKENS_PER_SMALL_FILE

    def estimate_cascade_cost(self, files: List[Path]) -> float:
        """
        Predict cost BEFORE any LLM calls.
        Conservative estimate: over-estimate slightly to stay under budget.
        """
        token_estimate = sum(self._quick_token_estimate(Path(f) if not isinstance(f, Path) else f) for f in files)
        base_cost = token_estimate * COST_PER_MILLION_8B / 1_000_000
        # Add 20% buffer for potential 70B escalations
        return base_cost * 1.2

    def on_file_save(self, path: Path) -> None:
        """Called by IDE integration or file watcher."""
        path = Path(path)
        relevant = self.should_trigger([path])
        if not relevant:
            self.audit.log(
                "skip",
                reason="all_files_ignored",
                files=[str(path)],
            )
            return

        estimated = self.estimate_cascade_cost(relevant)
        if not self.config.should_process(estimated, hourly_spend=self.audit.hourly_spend()):
            self.audit.log(
                "skip",
                reason="cost_exceeds_limit",
                estimated_cost=estimated,
                session_id=str(uuid.uuid4())[:8],
            )
            return

        session_id = str(uuid.uuid4())[:8]
        self.audit.log(
            "trigger",
            event="on-save",
            session_id=session_id,
            files=[str(p) for p in relevant],
            estimated_cost=estimated,
            config=self.config.to_dict(),
        )
        for file in relevant:
            self._process_file(file, session_id)

    def on_git_commit(self, changed_files: List[Path]) -> None:
        """Called by git hook or CI."""
        changed_paths = [Path(f) if not isinstance(f, Path) else f for f in changed_files]
        relevant = self.should_trigger(changed_paths)
        if not relevant:
            self.audit.log(
                "skip",
                reason="all_files_ignored",
                files=[str(f) for f in changed_paths],
            )
            return

        estimated = self.estimate_cascade_cost(relevant)

        if not self.config.should_process(estimated, hourly_spend=self.audit.hourly_spend()):
            limit = self.config.effective_max_cost()
            self.audit.log(
                "skip",
                reason="cost_exceeds_limit",
                estimated_cost=estimated,
                limit=limit,
            )
            self.notify(f"Skipped: ${estimated:.4f} > limit ${limit:.4f}")
            return

        limits = self.config.get("limits") or {}
        hourly_budget = min(
            float(limits.get("hourly_budget", 1.0)),
            HARD_MAX_HOURLY_BUDGET,
        )
        if self.audit.hourly_spend() + estimated > hourly_budget:
            self.audit.log("skip", reason="hourly_budget_exhausted")
            return

        session_id = str(uuid.uuid4())[:8]
        self.audit.log(
            "trigger",
            event="on-commit",
            session_id=session_id,
            files=[str(f) for f in relevant],
            estimated_cost=estimated,
            config=self.config.to_dict(),
        )

        for file in relevant:
            self._process_file(file, session_id)

    def estimate_task_nav_cost(self) -> float:
        """Estimated cost for task-based navigation (8B + retry + possible 70B)."""
        return TASK_NAV_ESTIMATED_COST

    def _list_python_files(self, entry: Optional[Path], limit: int = 50) -> List[str]:
        """List Python files for context. If entry given, scope to that dir."""
        base = (self.repo_root / entry) if entry else self.repo_root
        if not base.exists():
            return []
        paths: List[str] = []
        for p in base.rglob("*.py"):
            if len(paths) >= limit:
                break
            try:
                rel = str(p.relative_to(self.repo_root))
            except ValueError:
                rel = str(p)
            if "test" in rel.lower() or "__pycache__" in rel:
                continue
            paths.append(rel)
        return paths[:limit]

    def _parse_nav_json(self, content: str) -> dict:
        """Extract JSON from LLM response (may be wrapped in markdown)."""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"file": "", "function": "", "line": 0, "confidence": 0}

    async def navigate_task(
        self,
        task: str,
        entry: Optional[Path] = None,
        llm_client: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        Task-based navigation for CLI. Returns result dict or None if cost limit exceeded.
        Entry point for scout-nav --task.
        """
        estimated = self.estimate_task_nav_cost()
        if not self.config.should_process(estimated, hourly_spend=self.audit.hourly_spend()):
            self.audit.log("skip", reason="manual_trigger_cost_limit", estimated_cost=estimated)
            return None

        import time

        from vivarium.scout.llm import call_groq_async

        session_id = str(uuid.uuid4())[:8]
        self.audit.log(
            "trigger",
            event="manual",
            session_id=session_id,
            task=task,
            estimated_cost=estimated,
            config=self.config.to_dict(),
        )

        file_list = self._list_python_files(entry)
        prompt = f"""Task: {task}

Repo root: {self.repo_root}
Files in scope (up to 50):
{chr(10).join(file_list)}

Respond with JSON only:
{{"file": "<path relative to repo>", "function": "<name>", "line": <number>, "confidence": <0-100>, "reasoning": "<brief>", "suggestion": "<what to check>"}}
"""

        retries = 0
        escalated = False
        model_used = "llama-3.1-8b-instant"
        total_cost = 0.0
        total_duration_ms = 0
        start = time.perf_counter()

        response = await call_groq_async(prompt, model=model_used, llm_client=llm_client)
        total_cost += response.cost_usd
        total_duration_ms = int((time.perf_counter() - start) * 1000)

        self.audit.log(
            "nav",
            session_id=session_id,
            model=model_used,
            cost=response.cost_usd,
            duration_ms=total_duration_ms,
        )

        suggestion = self._parse_nav_json(response.content)
        suggestion.setdefault("confidence", 85)
        suggestion.setdefault("reasoning", "")
        suggestion.setdefault("suggestion", "")

        validation = self.validator.validate(suggestion, repo_root=self.repo_root)
        self.audit.log(
            "validation",
            session_id=session_id,
            is_valid=validation.is_valid,
            error_code=validation.error_code if not validation.is_valid else None,
        )

        if not validation.is_valid and validation.alternatives:
            retries += 1
            prompt += f"\nPrevious failed: {validation.error_code}. Alternatives: {validation.alternatives[:3]}"
            response = await call_groq_async(prompt, model=model_used, llm_client=llm_client)
            total_cost += response.cost_usd
            total_duration_ms = int((time.perf_counter() - start) * 1000)
            self.audit.log("nav_retry", session_id=session_id, model=model_used, attempt=2, cost=response.cost_usd)
            suggestion = self._parse_nav_json(response.content)
            suggestion.setdefault("confidence", 85)
            suggestion.setdefault("reasoning", "")
            suggestion.setdefault("suggestion", "")
            validation = self.validator.validate(suggestion, repo_root=self.repo_root)

        if not validation.is_valid:
            escalated = True
            model_used = "llama-3.3-70b-versatile"
            response = await call_groq_async(prompt, model=model_used, llm_client=llm_client)
            total_cost += response.cost_usd
            total_duration_ms = int((time.perf_counter() - start) * 1000)
            self.audit.log(
                "nav_escalate",
                session_id=session_id,
                model=model_used,
                cost=response.cost_usd,
                reason="persistent_validation_failure",
            )
            suggestion = self._parse_nav_json(response.content)
            suggestion.setdefault("confidence", 85)
            suggestion.setdefault("reasoning", "")
            suggestion.setdefault("suggestion", "")
            validation = self.validator.validate(suggestion, repo_root=self.repo_root)

        if validation.actual_file:
            try:
                target_file = str(validation.actual_file.relative_to(self.repo_root))
            except ValueError:
                target_file = str(validation.actual_file)
        else:
            target_file = suggestion.get("file", "")

        target_line = validation.actual_line or suggestion.get("line", 0)
        signature = validation.symbol_snippet or ""

        return {
            "task": task,
            "target_file": target_file,
            "target_function": suggestion.get("function", ""),
            "line_estimate": target_line,
            "signature": signature,
            "confidence": validation.adjusted_confidence if validation.is_valid else suggestion.get("confidence", 0),
            "model_used": model_used,
            "cost_usd": total_cost,
            "duration_ms": total_duration_ms,
            "retries": retries,
            "escalated": escalated,
            "related_files": [],
            "reasoning": suggestion.get("reasoning", ""),
            "suggestion": suggestion.get("suggestion", ""),
            "session_id": session_id,
        }

    def on_manual_trigger(self, files: List[Path], task: str = None) -> None:
        """Called by CLI scout-nav, scout-brief."""
        file_paths = [Path(f) if not isinstance(f, Path) else f for f in files]
        relevant = self.should_trigger(file_paths)
        if not relevant:
            self.audit.log(
                "skip",
                reason="all_files_ignored",
                files=[str(f) for f in file_paths],
            )
            return

        estimated = self.estimate_cascade_cost(relevant)
        if not self.config.should_process(estimated, hourly_spend=self.audit.hourly_spend()):
            self.audit.log(
                "skip",
                reason="cost_exceeds_limit",
                estimated_cost=estimated,
                limit=self.config.effective_max_cost(),
            )
            return

        session_id = str(uuid.uuid4())[:8]
        self.audit.log(
            "trigger",
            event="manual",
            session_id=session_id,
            files=[str(f) for f in relevant],
            estimated_cost=estimated,
            task=task,
            config=self.config.to_dict(),
        )
        for file in relevant:
            self._process_file(file, session_id)

    def _quick_parse(self, file: Path) -> str:
        """Quick parse for context (extract signatures, exports)."""
        try:
            if not file.exists():
                return ""
            content = file.read_text(encoding="utf-8", errors="replace")
            return content[:2000]
        except OSError:
            return ""

    def _scout_nav(self, file: Path, context: str, model: str = "8b") -> NavResult:
        """Generate nav suggestion (stub — real impl in scout-nav-cli)."""
        # Stub: return a valid suggestion for testing
        try:
            rel = str(file.relative_to(self.repo_root))
        except ValueError:
            rel = str(file)
        cost = 0.0002 if model == "8b" else 0.0009
        return NavResult(
            suggestion={"file": rel, "function": "main", "line": 1, "confidence": 90},
            cost=cost,
            duration_ms=50,
            signature_changed=False,
            new_exports=False,
        )

    def _affects_module_boundary(self, file: Path, nav_result: NavResult) -> bool:
        """Detect if change affects module interface."""
        return (
            nav_result.signature_changed
            or nav_result.new_exports
            or self._is_public_api(file)
        )

    def _is_public_api(self, file: Path) -> bool:
        """Heuristic: file is in public API directory."""
        try:
            rel = str(file.relative_to(self.repo_root))
            return "runtime" in rel or rel.startswith("vivarium/") and "test" not in rel
        except ValueError:
            return False

    def _detect_module(self, file: Path) -> str:
        """Detect module name from file path."""
        try:
            rel = file.relative_to(self.repo_root)
            parts = rel.parts
            if len(parts) >= 2:
                return parts[0]
            return rel.stem or "unknown"
        except ValueError:
            return file.stem or "unknown"

    def _critical_path_files(self) -> set:
        """Files considered critical (triggers PR draft)."""
        # Stub: check for SYSTEM or runtime files
        return set()

    def _generate_symbol_doc(self, file: Path, nav_result: NavResult, validation: ValidationResult) -> SymbolDoc:
        """Generate symbol doc (stub — real impl in scout-brief)."""
        cost = 0.0002
        return SymbolDoc(content=f"# {file.name}\n\nGenerated doc.", generation_cost=cost)

    def _write_draft(self, file: Path, symbol_doc: SymbolDoc) -> Path:
        """Write draft to docs/drafts/."""
        draft_dir = self.repo_root / "docs" / "drafts"
        draft_dir.mkdir(parents=True, exist_ok=True)
        try:
            rel = file.relative_to(self.repo_root)
            draft_path = draft_dir / f"{rel.stem}.md"
        except ValueError:
            draft_path = draft_dir / f"{file.stem}.md"
        draft_path.write_text(symbol_doc.content, encoding="utf-8")
        return draft_path

    def _update_module_brief(self, module: str, trigger_file: Path, session_id: str) -> float:
        """Update docs/drafts/modules/{module}.md."""
        cost = BRIEF_COST_PER_FILE
        modules_dir = self.repo_root / "docs" / "drafts" / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        brief_path = modules_dir / f"{module}.md"
        content = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
        if not content:
            content = f"# Module: {module}\n\n"
        content += f"\n<!-- Updated by {trigger_file} -->\n"
        brief_path.write_text(content, encoding="utf-8")
        return cost

    def _create_human_ticket(self, file: Path, nav_result: NavResult, validation: ValidationResult) -> None:
        """Create human escalation ticket (stub)."""
        ticket_path = self.repo_root / "docs" / "drafts" / ".scout-escalations"
        ticket_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ticket_path, "a", encoding="utf-8") as f:
            f.write(f"ESCALATION: {file} - {validation.error_code}\n")

    def _create_pr_draft(self, module: str, file: Path, session_id: str) -> None:
        """Create PR draft for critical path (stub)."""
        pass

    def _process_file(self, file: Path, session_id: str) -> None:
        """Process single file: nav → validate → brief → cascade."""
        context = self._quick_parse(file)

        nav_result = self._scout_nav(file, context, model="8b")
        self.audit.log(
            "nav",
            session_id=session_id,
            model="llama-3.1-8b",
            cost=nav_result.cost,
            duration_ms=nav_result.duration_ms,
        )

        validation = self.validator.validate(nav_result.suggestion, repo_root=self.repo_root)
        self.audit.log(
            "validation",
            session_id=session_id,
            is_valid=validation.is_valid,
            error_code=validation.error_code if not validation.is_valid else None,
        )

        if not validation.is_valid:
            if validation.alternatives:
                context += f"\nPrevious failed: {validation.error_code}"
                context += f"\nAlternatives: {validation.alternatives[:3]}"
                nav_result = self._scout_nav(file, context, model="8b")
                self.audit.log(
                    "nav_retry",
                    session_id=session_id,
                    model="llama-3.1-8b",
                    attempt=2,
                    cost=nav_result.cost,
                )
                validation = self.validator.validate(nav_result.suggestion, repo_root=self.repo_root)
                if validation.is_valid:
                    self.audit.log("validation_retry_success", session_id=session_id, attempt=2)

            if not validation.is_valid:
                nav_result = self._scout_nav(file, context, model="70b")
                self.audit.log(
                    "nav_escalate",
                    session_id=session_id,
                    model="llama-3.1-70b",
                    cost=nav_result.cost,
                    reason="persistent_validation_failure",
                )
                validation = self.validator.validate(nav_result.suggestion, repo_root=self.repo_root)

        if not validation.is_valid:
            self.audit.log(
                "escalate_human",
                session_id=session_id,
                reason="max_retries_exceeded",
                final_error=validation.error_code,
            )
            self._create_human_ticket(file, nav_result, validation)
            return

        symbol_doc = self._generate_symbol_doc(file, nav_result, validation)
        draft_path = self._write_draft(file, symbol_doc)
        self.audit.log(
            "cascade_symbol",
            session_id=session_id,
            file=str(file),
            draft_path=str(draft_path),
            cost=symbol_doc.generation_cost,
        )

        if self._affects_module_boundary(file, nav_result):
            module = self._detect_module(file)
            brief_cost = self._update_module_brief(module, file, session_id)
            self.audit.log(
                "cascade_module",
                session_id=session_id,
                module=module,
                trigger_file=str(file),
                cost=brief_cost,
            )
            if file in self._critical_path_files():
                self._create_pr_draft(module, file, session_id)
