# META LESSONS LEARNED  
*Date: 2026‑02‑04*  

## 1. Clear Scope Definition Wins  
- **Pattern:** Tasks that began with an explicit “output format” and constraints finished without re‑work.  
- **Lesson:** Always start each sub‑task with a one‑sentence scope and a concrete output specification (file path, format, naming).

## 2. Incremental Prompting Reduces Ambiguity  
- **Pattern:** When the prompt asked for “generalizable lessons” and then listed formatting rules, the model produced a focused, well‑structured document.  
- **Lesson:** Break complex deliverables into small, ordered directives (e.g., “list patterns → summarize → format”).

## 3. Leverage Existing Directory Structure  
- **Pattern:** All new artifacts were placed under `experiments/<exp_id>/`, keeping the repo clean and avoiding accidental edits to read‑only core files.  
- **Lesson:** Default to the experiment‑specific folder unless a cross‑experiment asset is explicitly required.

## 4. Consistent Naming Conventions Aid Discovery  
- **Pattern:** Files named `META_LESSONS_LEARNED.md` were instantly recognizable across runs.  
- **Lesson:** Adopt a canonical naming scheme for recurring artifacts (e.g., `META_*.md`, `RESULTS_*.json`).

## 5. Minimalist Language Improves Speed  
- **Pattern:** Concise bullet points and short sentences produced the needed insight faster than verbose paragraphs.  
- **Lesson:** When the goal is knowledge capture, prefer terse, actionable statements over narrative exposition.

## 6. Explicit “Read‑Only” Awareness Prevents Errors  
- **Pattern:** No attempts were made to modify `grind_spawner*.py` or `safety_*.py`.  
- **Lesson:** Encode file‑access rules in the prompt; the model will respect them automatically.

## 7. Reuse of Prior Patterns Accelerates Learning  
- **Pattern:** The same “output format → artifact wrapper” pattern was reused across multiple experiments with no failures.  
- **Lesson:** Codify this pattern in a template file (e.g., `templates/artifact_wrapper.md`) for future runs.

## 8. Quick Validation Loop  
- **Pattern:** Immediate verification of the artifact path and type prevented downstream path‑resolution bugs.  
- **Lesson:** After each creation step, run a lightweight sanity check (exists? correct extension?).

## 9. Document Evolution, Not Just Results  
- **Pattern:** The meta‑lesson file captures *how* we arrived at the solution, not only the solution itself.  
- **Lesson:** Future swarm runs should always generate a “lessons learned” artifact at the end of each cycle.

---

*End of META_LESSONS_LEARNED.md*