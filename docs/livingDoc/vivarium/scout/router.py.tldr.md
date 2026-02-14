<!-- FACT_CHECKSUM: 94098d66ea9df0466a683fffa46f0ecc365bccac71215f4942f48c51759b40f1 -->

# ELIV
This module provides work coordination, resource limits, activity logging.

## Module Constants
- `BRIEF_COST_PER_FILE`: 0.005 (used at line 723)
- `COST_PER_MILLION_70B`: 0.9 (used at lines none)
- `COST_PER_MILLION_8B`: 0.2 (used at line 157)
- `DRAFT_COST_PER_FILE`: 0.0004 (used at lines 270, 281)
- `logger`: (used at lines 322, 774, 785, 820, 846, 848)
- `TASK_NAV_ESTIMATED_COST`: 0.002 (used at line 342)
- `TOKENS_PER_SMALL_FILE`: 500 (used at lines 144, 149)

# BudgetExhaustedError
Raised when hourly budget is exhausted before an LLM operation.

## Constants
- (none)

## Methods
- (none)

# NavResult
Result of scout-nav LLM call.

## Constants
- (none)

## Methods
- (none)

# SymbolDoc
Generated symbol documentation.

## Constants
- (none)

## Methods
- (none)

# TriggerRouter
Orchestrates triggers, respects limits, prevents infinite loops, and cascades doc updates safely.

## Constants
- (none)

## Methods
- `__init__(self, config: ScoutConfig=None, audit: AuditLog=None, validator: Validator=None, repo_root: Path=None, notify: Callable[[str], None]=None)`: 
  Orchestrates triggers, respects limits, prevents infinite loops, and cascades doc updates safely.
- `should_trigger(self)`: 
  (no description)
- `_quick_token_estimate(self)`: 
  (no description)
- `estimate_cascade_cost(self)`: 
  (no description)
- `on_file_save(self)`: 
  (no description)
- `on_git_commit(self)`: 
  (no description)
- `prepare_commit_msg(self)`: 
  (no description)
- `estimate_task_nav_cost(self)`: 
  (no description)
- `_list_python_files(self)`: 
  (no description)
- `_parse_nav_json(self)`: 
  (no description)
- `navigate_task(self)`: 
  (no description)
- `on_manual_trigger(self)`: 
  (no description)
- `_quick_parse(self)`: 
  (no description)
- `_scout_nav(self)`: 
  (no description)
- `_affects_module_boundary(self)`: 
  (no description)
- `_is_public_api(self)`: 
  (no description)
- `_detect_module(self)`: 
  (no description)
- `_critical_path_files(self)`: 
  (no description)
- `_generate_symbol_doc(self)`: 
  (no description)
- `_write_draft(self)`: 
  (no description)
- `_update_module_brief(self)`: 
  (no description)
- `_create_human_ticket(self)`: 
  (no description)
- `_create_pr_draft(self)`: 
  (no description)
- `_generate_commit_draft(self)`: 
  (no description)
- `_generate_pr_snippet(self)`: 
  (no description)
- `_generate_impact_summary(self)`: 
  (no description)
- `_process_file(self)`: 
  (no description)

# _notify_user
Notify user (stub — override for testing or real UI).

## Constants
- (none)

## Methods
- `_notify_user(self, message: str) -> None`: 
  Notify user (stub — override for testing or real UI).

# check_budget_with_message
Check if operation can proceed within hourly budget.

## Constants
- (none)

## Methods
- `check_budget_with_message(self, config: ScoutConfig, estimated_cost: float=0.01, audit: Optional[AuditLog]=None) -> bool`: 
  Check if operation can proceed within hourly budget.

# on_git_commit
Proactive echo: invalidate dependency graph for changed files. Called by post-commit hook — runs in <100ms, no LLM cost.

## Constants
- (none)

## Methods
- `on_git_commit(self, changed_files: List[Path], repo_root: Optional[Path]=None) -> None`: 
  Proactive echo: invalidate dependency graph for changed files. Called by post-commit hook — runs in <100ms, no LLM cost.