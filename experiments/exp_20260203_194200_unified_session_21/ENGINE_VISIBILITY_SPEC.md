# Engine Visibility Specification

## Overview
The dashboard now surfaces the inference engine and model used by each worker node, together with the reason the engine was selected. Real‑time updates are streamed via Server‑Sent Events (SSE).

## UI Changes
- **Node Card**  
  Each node card displays:
  - **Engine badge** – blue “CLAUDE” badge or pink “GROQ” badge.
  - **Model name** – e.g., `claude-sonnet-4`, `llama-3.3-70b`.
  - **Selection reason** – free‑text explanation.
  - **Tokens used** and **cost accrued** for that node.

- **Summary Panel**  
  Shows:
  - Claude vs Groq usage split (percentage, token count, cost).
  - Cost breakdown per engine.
  - Simple bar chart of token distribution across models.

## Real‑time Data Flow
1. **Backend (`progress_server.py`)** maintains in‑memory state for each node and aggregate summary.
2. When the orchestrator calls `update_node(...)`, the server:
   - Updates node‑specific data.
   - Updates aggregate counters.
   - Emits two SSE events:
     - `node_update` – payload contains the updated node object.
     - `summary_update` – payload contains the full usage summary.
3. **Frontend (`dashboard.html`)** opens an `EventSource` to `/sse/updates` and:
   - Renders/updates node cards on `node_update`.
   - Refreshes the summary panel on `summary_update`.

## Integration Points
- **Backend** – expose `update_node` function for the rest of the system (e.g., orchestrator) to report engine/model switches, token usage, and cost.
- **Frontend** – the SSE endpoint is `/sse/updates`. No additional JS libraries are required; vanilla JS handles rendering.

## Files Added / Modified
| Path | Change |
|------|--------|
| `experiments/exp_20260203_194200_unified_session_21/dashboard.html` | Added node card UI, badges, SSE client, and summary panel. |
| `experiments/exp_20260203_194200_unified_session_21/progress_server.py` | Implemented SSE endpoint, in‑memory state, `update_node` API, and broadcasting logic. |
| `experiments/exp_20260203_194200_unified_session_21/ENGINE_VISIBILITY_SPEC.md` | Documentation of the new feature. |

## Future Enhancements
- Replace the placeholder Canvas bar chart with a full‑featured Chart.js visualization.
- Persist state to a database for crash‑recovery.
- Add authentication to the SSE endpoint if required.

--- 

*All changes are confined to the experiment directory; core system files remain read‑only.*