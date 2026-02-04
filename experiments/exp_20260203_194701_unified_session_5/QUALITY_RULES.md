# Quality Rules

## Purpose
The purpose of these quality rules is to ensure that the swarm never does anything stupid.

## Rules
1. Never output markdown code fences (```python) in actual code files.
2. Never overwrite a complex file with a simpler version.
3. Never use placeholder logic like `random()` when real logic is needed.
4. Never leave TODO comments without implementing.
5. Always validate output is syntactically correct before saving.
6. Always check if a file exists and is larger before overwriting.
7. Strip any markdown formatting from code output.

## Implementation
These rules will be enforced by the `quality_validator.py` script.