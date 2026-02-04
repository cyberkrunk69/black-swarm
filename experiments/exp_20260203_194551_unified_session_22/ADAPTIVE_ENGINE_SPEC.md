# Adaptive Engine Selection Specification

## 1. Complexity Analysis
- **Simple tasks** (e.g., `create file`, `fix typo`) → **Groq** (cheap, fast)  
- **Complex tasks** (e.g., `design`, `refactor`, `security`) → **Claude** (smart)

## 2. Budget Awareness
- **Low remaining budget** → **Groq**  
- **Critical task** *and* sufficient budget → **Claude**

## 3. Explicit Override
- If the task description contains **`use groq`** → **Force Groq**  
- If the task description contains **`use claude`** → **Force Claude**

## 4. Quality Feedback
- If a **Groq**‑generated output fails verification → **Retry with Claude**  
- The system records failures to **learn patterns** and improve future selections.

---

*The selector below implements the above rules and provides a hook for verification feedback.*