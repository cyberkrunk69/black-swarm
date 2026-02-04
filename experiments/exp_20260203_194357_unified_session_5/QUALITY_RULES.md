# Quality Rules

## Purpose
The purpose of these quality rules is to ensure that the codebase remains maintainable, efficient, and free of avoidable errors.

## Rules

1. **No Markdown Code Fences in Code Files** – Never output markdown code fences (```python) in actual code files.  
2. **Preserve Complexity** – Never overwrite a complex file with a simpler version.  
3. **No Placeholder Logic** – Never use placeholder logic like `random()` when real logic is needed.  
4. **Implement TODOs** – Never leave `TODO` comments without implementing the required functionality.  
5. **Syntactic Validation** – Always validate that output is syntactically correct before saving.  
6. **Safe Overwrite** – Always check if a file exists and is larger before overwriting it.  
7. **Strip Markdown Formatting** – Strip any markdown formatting from code output before writing to disk.

## Core System Files
Core system files (e.g., `grind_spawner.py`, `orchestrator.py`) are **READ‑ONLY**.

## New File Location
New files go to `experiments/exp_20260203_194357_unified_session_5/` by default.