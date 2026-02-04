import json
import asyncio
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect

# Store active WebSocket connections
_ws_connections: Set[WebSocket] = set()

# Store queues for Server‑Sent Events listeners
_sse_queues: Set[asyncio.Queue] = set()


async def broadcast(event: dict) -> None:
    """
    Send a JSON‑encoded event to all WebSocket clients and push it onto
    every SSE queue.
    """
    payload = json.dumps(event)

    # ---- WebSocket broadcast ----
    dead_ws = []
    for ws in _ws_connections:
        try:
            await ws.send_text(payload)
        except Exception:
            dead_ws.append(ws)
    for ws in dead_ws:
        _ws_connections.discard(ws)

    # ---- SSE broadcast ----
    for q in _sse_queues:
        await q.put(payload)


async def register_ws(ws: WebSocket) -> None:
    """Accept the connection and add it to the active set."""
    await ws.accept()
    _ws_connections.add(ws)


def unregister_ws(ws: WebSocket) -> None:
    """Remove a WebSocket from the active set."""
    _ws_connections.discard(ws)


def register_sse_queue(q: asyncio.Queue) -> None:
    """Add a new SSE queue."""
    _sse_queues.add(q)


def unregister_sse_queue(q: asyncio.Queue) -> None:
    """Remove an SSE queue when the client disconnects."""
    _sse_queues.discard(q)