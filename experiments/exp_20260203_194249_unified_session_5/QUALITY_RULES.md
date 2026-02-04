# Quality Rules

## Purpose
The purpose of these quality rules is to ensure that the swarm never does anything stupid.

## Rules
1. **Never output markdown code fences** (```python) in actual code files.  
2. **Never overwrite a complex file with a simpler version** – only replace when the new content is demonstrably more complete.  
3. **Never use placeholder logic** (e.g., `random()`) when real logic is required.  
4. **Never leave TODO comments** without implementing the required functionality.  
5. **Always validate output is syntactically correct** before saving any code file.  
6. **Always check if a file exists and is larger** before overwriting; only overwrite when the new file is at least as large and passes complexity checks.  
7. **Strip any markdown formatting** from code output before writing to disk.

## Implementation
These rules are enforced by the `quality_validator.py` utility located in the same experiment directory. The validator provides functions to:

- Detect markdown fences.
- Verify Python syntax via `ast.parse`.
- Compare file size/complexity before overwriting.
- Remove markdown formatting from generated code.

The validator should be invoked by any automated code‑generation step to guarantee compliance with the above rules.