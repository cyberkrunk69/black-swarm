#!/usr/bin/env python3
"""
Progress server for the unified session dashboard.
Provides:
- HTTP endpoint for the dashboard HTML.
- Server‑Sent Events (SSE) endpoint that streams per‑node engine/model updates
  and aggregate usage summary.
"""

import json
import asyncio
from collections import defaultdict
from aiohttp import web

# ----------------------------------------------------------------------
# In‑memory state (for demo purposes – replace with real data sources)
# ----------------------------------------------------------------------
nodes_state = {}
summary_state = {
    "claude": {"tokens": 0, "cost": 0.0, "percent": 0},
    "groq":   {"tokens": 0, "cost": 0.0, "percent": 0},
    "models": defaultdict(lambda: {"tokens":0, "cost":0.0})
}

# ----------------------------------------------------------------------
# Helper to push updates to all connected SSE clients
# ----------------------------------------------------------------------
sse_clients = set()

async def broadcast(event):
    data = f"data: {json.dumps(event)}\n\n"
    for resp in list(sse_clients):
        try:
            await resp.write(data.encode())
        except Exception:
            sse_clients.discard(resp)

# ----------------------------------------------------------------------
# Public API used by the rest of the system (e.g., orchestrator) to
# report node status changes.
# ----------------------------------------------------------------------
def update_node(node_id, engine, model, reason, tokens_delta, cost_delta):
    """Update internal state and push an SSE message."""
    node = nodes_state.get(node_id, {
        "id": node_id,
        "engine": engine,
        "model": model,
        "reason": reason,
        "tokens": 0,
        "cost": 0.0
    })
    node.update({
        "engine": engine,
        "model": model,
        "reason": reason,
        "tokens": node["tokens"] + tokens_delta,
        "cost": node["cost"] + cost_delta
    })
    nodes_state[node_id] = node

    # Update aggregate summary
    eng_key = engine.lower()
    summary_state[eng_key]["tokens"] += tokens_delta
    summary_state[eng_key]["cost"]   += cost_delta

    model_entry = summary_state["models"][model]
    model_entry["tokens"] += tokens_delta
    model_entry["cost"]   += cost_delta

    # Re‑calculate percentages
    total_tokens = summary_state["claude"]["tokens"] + summary_state["groq"]["tokens"]
    if total_tokens:
        summary_state["claude"]["percent"] = round(100 * summary_state["claude"]["tokens"] / total_tokens, 1)
        summary_state["groq"]["percent"]   = round(100 * summary_state["groq"]["tokens"]   / total_tokens, 1)

    # Push node update
    asyncio.create_task(broadcast({
        "type": "node_update",
        "node": node
    }))

    # Push summary update (debounced in a real system; immediate here for simplicity)
    asyncio.create_task(broadcast({
        "type": "summary_update",
        "summary": {
            "claude": summary_state["claude"],
            "groq":   summary_state["groq"],
            "models": dict(summary_state["models"])
        }
    }))

# ----------------------------------------------------------------------
# HTTP Handlers
# ----------------------------------------------------------------------
async def index(request):
    """Serve the dashboard HTML."""
    return web.FileResponse('experiments/exp_20260203_194200_unified_session_21/dashboard.html')

async def sse_handler(request):
    """SSE endpoint that streams JSON events."""
    resp = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )
    await resp.prepare(request)
    sse_clients.add(resp)

    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(30)  # heartbeat
            await resp.write(b":heartbeat\n\n")
    except asyncio.CancelledError:
        pass
    finally:
        sse_clients.discard(resp)
    return resp

# ----------------------------------------------------------------------
# App setup
# ----------------------------------------------------------------------
app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/sse/updates', sse_handler)

# ----------------------------------------------------------------------
# If this file is executed directly, start the server.
# ----------------------------------------------------------------------
if __name__ == '__main__':
    web.run_app(app, port=8080)