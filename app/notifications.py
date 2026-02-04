import asyncio
from typing import List, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse

# Global manager for WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Send a JSON‑serializable message to all connected clients."""
        if not self.active_connections:
            return
        data = json.dumps(message)
        await asyncio.gather(
            *[connection.send_text(data) for connection in self.active_connections],
            return_exceptions=True,
        )

manager = ConnectionManager()

# Helper to push events from anywhere in the codebase
async def push_event(event_type: str, payload: Dict[str, Any] = None):
    """Broadcast an event to WebSocket clients (and SSE fallback)."""
    if payload is None:
        payload = {}
    await manager.broadcast({"event": event_type, "data": payload})

# SSE implementation – a simple async generator
async def sse_event_generator(request: Request):
    """Yield Server‑Sent Events. Each line is a JSON payload prefixed with 'data: '."""
    queue: asyncio.Queue = asyncio.Queue()

    # Register a temporary listener that puts messages into the queue
    async def listener(message: Dict[str, Any]):
        await queue.put(message)

    # Attach listener to the manager (so SSE and WS share the same source)
    manager_sse_listeners.append(listener)

    try:
        while True:
            # If client disconnects, exit
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                # Keep‑alive comment to prevent proxies from closing the connection
                yield ": keep-alive\n\n"
    finally:
        # Clean up listener on disconnect
        manager_sse_listeners.remove(listener)

# Internal list of SSE listeners – each listener is a coroutine that receives a dict
manager_sse_listeners: List[callable] = []

# Hook manager.broadcast to also push to SSE listeners
_original_broadcast = manager.broadcast

async def _broadcast_with_sse(message: Dict[str, Any]):
    await _original_broadcast(message)
    # Push to all SSE listeners
    await asyncio.gather(
        *[listener(message) for listener in manager_sse_listeners],
        return_exceptions=True,
    )

manager.broadcast = _broadcast_with_sse  # type: ignore