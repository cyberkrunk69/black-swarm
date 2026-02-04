# Quality Rules

## Purpose
The purpose of these quality rules is to ensure that the codebase remains maintainable, efficient, and free of common mistakes.

## Rules
1. **No Markdown Code Fences in Code Files**  
   Never output markdown code fences (```python) in actual code files.

2. **Never Overwrite Complex Files with Simpler Versions**  
   Do not replace a file that contains more content or complexity with a shorter, simpler version.

3. **No Placeholder Logic**  
   Do not use placeholder functions such as `random()` when real, deterministic logic is required.

4. **Implement All TODOs**  
   All `TODO` comments must be resolved before committing code.

5. **Validate Syntax Before Saving**  
   Ensure the code is syntactically correct (e.g., passes `ast.parse`) before writing to disk.

6. **Check Existing Files Before Overwrite**  
   If a target file already exists, only overwrite it when the new content is at least as large (or more complex) as the existing content.

7. **Strip Markdown Formatting**  
   Remove any markdown formatting (code fences, headings, etc.) from code before saving.

## Core System Files
Core system files (e.g., `grind_spawner.py`, `orchestrator.py`, etc.) are **READ‑ONLY**.

## New File Location
All new files should be placed under `experiments/exp_20260203_194046_unified_session_5/` by default.