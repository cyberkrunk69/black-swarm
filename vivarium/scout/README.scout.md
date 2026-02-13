# Scout: Autonomous Dev Partner

## Origin

Born from a single pain point: "Hey this sucks—write me a tool that'll gen a repo map for the big LLM."

## Evolution

Grew into a self-documenting, self-explaining, self-critiquing dev loop through iterative refinement:

- Symbol-level living docs → commit/PR drafts → Git hooks → CI guardrails → full auditability

## Philosophy

- **Agnostic**: Works in any editor, with any LLM
- **Auditable**: Every decision logged, costed, and confidence-scored
- **Autonomous**: Drafts generated pre-commit; human-in-the-loop for final approval

## Key Components

- `router.py`: Orchestrates doc generation, draft assembly, and Git integration
- `doc_generation.py`: Generates `.tldr.md`, `.deep.md`, `.eliv.md` from AST + LLM
- `git_drafts.py`: Assembles commit/PR messages from staged diffs + living docs
- `audit.py`: Tracks cost, confidence, and validation across all events
