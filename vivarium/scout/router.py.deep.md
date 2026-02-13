# router.py

## Class: `NavResult`

Detailed documentation (deep stub).

```python
class NavResult:
    """Result of scout-nav LLM call."""

    suggestion: dict
    cost: float
    duration_ms: int
    signature_changed: bool = False
    new_exports: bool = False
```

## Class: `SymbolDoc`

Detailed documentation (deep stub).

```python
class SymbolDoc:
    """Generated symbol documentation."""

    content: str
    generation_cost: float
```

## Function: `_notify_user`

Detailed documentation (deep stub).

```python
def _notify_user(message: str) -> None:
    """Notify user (stub — override for testing or real UI)."""
    # Could use logging, print, or IDE notification
    import logging

    logging.getLogger(__name__).info("Scout: %s", message)
```

## Class: `TriggerRouter`

Detailed documentation (deep stub).

```python
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
        self.validator = validator or Validator
```

## Function: `__init__`

Detailed documentation (deep stub).

```python
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
        self.ignore = IgnorePat
```

## Function: `should_trigger`

Detailed documentation (deep stub).

```python
    def should_trigger(self, files: List[Path]) -> List[Path]:
        """Filter ignored files, return relevant subset."""
        return [f for f in files if not self.ignore.matches(f, self.repo_root)]
```

## Function: `_quick_token_estimate`

Detailed documentation (deep stub).

```python
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
```

## Function: `estimate_cascade_cost`

Detailed documentation (deep stub).

```python
    def estimate_cascade_cost(self, files: List[Path]) -> float:
        """
        Predict cost BEFORE any LLM calls.
        Conservative estimate: over-estimate slightly to stay under budget.
        """
        token_estimate = sum(self._quick_token_estimate(Path(f) if not isinstance(f, Path) else f) for f in files)
        base_cost = token_estimate * COST_PER_MILLION_8B / 1_000_000
        # Add 20% buffer for potential 70B escalations
        return base_cost * 1.2
```

## Function: `on_file_save`

Detailed documentation (deep stub).

```python
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
        if not self.config.should_process(estimated, hourly_spend=self.audi
```

## Function: `on_git_commit`

Detailed documentation (deep stub).

```python
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

        estimated = self.estimate_cascade
```

## Function: `estimate_task_nav_cost`

Detailed documentation (deep stub).

```python
    def estimate_task_nav_cost(self) -> float:
        """Estimated cost for task-based navigation (8B + retry + possible 70B)."""
        return TASK_NAV_ESTIMATED_COST
```

## Function: `_list_python_files`

Detailed documentation (deep stub).

```python
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
            e
```

## Function: `_parse_nav_json`

Detailed documentation (deep stub).

```python
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
    
```

## Function: `navigate_task`

Detailed documentation (deep stub).

```python
    async def navigate_task(
        self,
        task: str,
        entry: Optional[Path] = None,
        llm_client: Optional[Callable] = None,
    ) -> Optional[dict]:
        """
        Task-based navigation for CLI. Returns result dict or None if cost limit exceeded.
        Entry point for scout-nav --task. Tries scout-index first (free), then LLM.
        """
        import time

        session_id = str(uuid.uuid4())[:8]

        # Try scout-index first (free, no cost limit)
        tr
```

## Function: `on_manual_trigger`

Detailed documentation (deep stub).

```python
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

        estimated = self.estimat
```

## Function: `_quick_parse`

Detailed documentation (deep stub).

```python
    def _quick_parse(self, file: Path) -> str:
        """Quick parse for context (extract signatures, exports)."""
        try:
            if not file.exists():
                return ""
            content = file.read_text(encoding="utf-8", errors="replace")
            return content[:2000]
        except OSError:
            return ""
```

## Function: `_scout_nav`

Detailed documentation (deep stub).

```python
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
```

## Function: `_affects_module_boundary`

Detailed documentation (deep stub).

```python
    def _affects_module_boundary(self, file: Path, nav_result: NavResult) -> bool:
        """Detect if change affects module interface."""
        return (
            nav_result.signature_changed
            or nav_result.new_exports
            or self._is_public_api(file)
        )
```

## Function: `_is_public_api`

Detailed documentation (deep stub).

```python
    def _is_public_api(self, file: Path) -> bool:
        """Heuristic: file is in public API directory."""
        try:
            rel = str(file.relative_to(self.repo_root))
            return "runtime" in rel or rel.startswith("vivarium/") and "test" not in rel
        except ValueError:
            return False
```

## Function: `_detect_module`

Detailed documentation (deep stub).

```python
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
```

## Function: `_critical_path_files`

Detailed documentation (deep stub).

```python
    def _critical_path_files(self) -> set:
        """Files considered critical (triggers PR draft)."""
        # Stub: check for SYSTEM or runtime files
        return set()
```

## Function: `_generate_symbol_doc`

Detailed documentation (deep stub).

```python
    def _generate_symbol_doc(self, file: Path, nav_result: NavResult, validation: ValidationResult) -> SymbolDoc:
        """Generate symbol doc (stub — real impl in scout-brief)."""
        cost = 0.0002
        return SymbolDoc(content=f"# {file.name}\n\nGenerated doc.", generation_cost=cost)
```

## Function: `_write_draft`

Detailed documentation (deep stub).

```python
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
        re
```

## Function: `_update_module_brief`

Detailed documentation (deep stub).

```python
    def _update_module_brief(self, module: str, trigger_file: Path, session_id: str) -> float:
        """Update docs/drafts/modules/{module}.md."""
        cost = BRIEF_COST_PER_FILE
        modules_dir = self.repo_root / "docs" / "drafts" / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        brief_path = modules_dir / f"{module}.md"
        content = brief_path.read_text(encoding="utf-8") if brief_path.exists() else ""
        if not content:
            content = f"# Modu
```

## Function: `_create_human_ticket`

Detailed documentation (deep stub).

```python
    def _create_human_ticket(self, file: Path, nav_result: NavResult, validation: ValidationResult) -> None:
        """Create human escalation ticket (stub)."""
        ticket_path = self.repo_root / "docs" / "drafts" / ".scout-escalations"
        ticket_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ticket_path, "a", encoding="utf-8") as f:
            f.write(f"ESCALATION: {file} - {validation.error_code}\n")
```

## Function: `_create_pr_draft`

Detailed documentation (deep stub).

```python
    def _create_pr_draft(self, module: str, file: Path, session_id: str) -> None:
        """Create PR draft for critical path (stub)."""
        pass
```

## Function: `_process_file`

Detailed documentation (deep stub).

```python
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

        validation = self.validator.validate(nav_resu
```
