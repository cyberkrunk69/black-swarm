# Adaptive Engine Selection Criteria

## Complexity Analysis
- Simple tasks (create file, fix typo) -> Groq (cheap, fast)
- Complex tasks (design, refactor, security) -> Claude (smart)

## Budget Awareness
- Low remaining budget -> Groq
- Critical task + budget available -> Claude

## Explicit Override
- Task contains 'use groq' -> Force Groq
- Task contains 'use claude' -> Force Claude

## Quality Feedback
- If Groq output fails verification -> Retry with Claude
- Learn patterns of which tasks need Claude