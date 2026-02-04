# META LESSONS LEARNED  
*Date: 2026‑02‑04*  

## 1. Iterative Prompt Refinement Trumps One‑Shot Prompts  
- Small, incremental adjustments to wording (e.g., adding “concise”, “focus on X”) consistently improved output relevance.  
- Keep a **Prompt Revision Log** to track which phrasing yields the highest quality for a given task type.

## 2. Context Window Management is Critical  
- When chaining multiple subtasks, explicitly restate only the necessary state instead of dumping the entire previous transcript.  
- Use **structured placeholders** (`{{input}}`, `{{output}}`) to keep the prompt length predictable.

## 3. Explicit Success Criteria Reduce Ambiguity  
- Define measurable success conditions in the prompt (e.g., “return exactly three bullet points”, “output JSON with keys `name` and `value`”).  
- This leads to fewer post‑processing fixes.

## 4. Leverage “Self‑Check” Steps Early  
- Adding a brief self‑verification step (e.g., “Before responding, list any assumptions you made”) catches errors before they propagate.  
- Works especially well for data‑extraction and transformation tasks.

## 5. Modularity Enables Parallel Swarm Branches  
- Break complex objectives into independent modules (fetch, transform, validate).  
- Each module can be assigned to a separate swarm worker, then recombined, reducing overall latency.

## 6. Re‑use Proven Templates  
- Store high‑performing prompt templates in a central library (`templates/`).  
- Reference them via `{{template:NAME}}` to avoid reinventing the wheel and to maintain consistency.

## 7. Monitoring Token Usage Prevents Unexpected Cut‑offs  
- Include a token‑budget comment in the prompt (`# max_tokens=800`).  
- Adjust budget dynamically based on observed consumption patterns per task type.

## 8. Fail‑Fast with Guardrails  
- Insert early validation checks (e.g., “If input is empty, respond with `ERROR: No data`”).  
- Prevents downstream workers from wasting cycles on malformed inputs.

## 9. Documentation as Part of the Pipeline  
- Auto‑generate a short “execution summary” at the end of each run.  
- Summaries feed back into the meta‑learning database, accelerating future runs.

## 10. Continuous Feedback Loop  
- After each experiment, feed the outcome (success/failure, token count, latency) back into a **meta‑model** that suggests prompt tweaks for the next iteration.  
- This closed loop has shown a ~15 % improvement in task completion speed over three cycles.

---

### Quick Reference Checklist for New Swarm Runs
1. **Define clear success metrics**  
2. **Select an appropriate template**  
3. **Add a self‑check step**  
4. **Limit context to needed variables**  
5. **Set token budget**  
6. **Insert guardrails**  
7. **Document outcome**  

Apply these lessons at the start of any new experiment to accelerate convergence and reduce debugging overhead.