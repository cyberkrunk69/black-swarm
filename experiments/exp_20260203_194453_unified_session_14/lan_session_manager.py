import asyncio
import logging
from datetime import datetime, timedelta

import websockets
from aiohttp import web

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages LAN sessions per IP address with isolation between
    "Your tasks" and "Network activity". Supports session timeout,
    real‑time updates via WebSocket, and a minimal dashboard.
    """

    def __init__(self):
        # Structure:
        # {
        #   ip_address: {
        #       "created_at": datetime,
        #       "timeout": datetime | None,
        #       "your_tasks": list,
        #       "network_activity": list,
        #   },
        #   ...
        # }
        self.sessions = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    async def create_session(self, ip_address: str, timeout_seconds: int | None = None):
        """Create a new session for the given IP, optionally with a timeout."""
        if ip_address not in self.sessions:
            timeout = (datetime.now() + timedelta(seconds=timeout_seconds)) if timeout_seconds else None
            self.sessions[ip_address] = {
                "created_at": datetime.now(),
                "timeout": timeout,
                "your_tasks": [],
                "network_activity": [],
            }
            logger.info(f"Session created for {ip_address}")
        else:
            logger.info(f"Session already exists for {ip_address}")

    async def delete_session(self, ip_address: str):
        """Remove a session and its data."""
        if ip_address in self.sessions:
            del self.sessions[ip_address]
            logger.info(f"Session deleted for {ip_address}")
        else:
            logger.info(f"No session found for {ip_address}")

    async def set_timeout(self, ip_address: str, timeout_seconds: int):
        """Update the timeout for an existing session."""
        if ip_address in self.sessions:
            self.sessions[ip_address]["timeout"] = datetime.now() + timedelta(seconds=timeout_seconds)
            logger.info(f"Timeout set for {ip_address} ({timeout_seconds}s)")
        else:
            logger.warning(f"Tried to set timeout on unknown session {ip_address}")

    async def _check_timeouts(self):
        """Internal: purge sessions whose timeout has elapsed."""
        now = datetime.now()
        for ip, data in list(self.sessions.items()):
            if data["timeout"] and now > data["timeout"]:
                await self.delete_session(ip)

    async def start(self):
        """Background task that periodically checks for expired sessions."""
        while True:
            await self._check_timeouts()
            await asyncio.sleep(1)

    # ------------------------------------------------------------------
    # Activity logging
    # ------------------------------------------------------------------
    async def add_task(self, ip_address: str, task: str):
        """Log a user‑level task for the given IP."""
        if ip_address in self.sessions:
            self.sessions[ip_address]["your_tasks"].append(
                {"task": task, "timestamp": datetime.now()}
            )
            logger.info(f"Task added for {ip_address}: {task}")
        else:
            logger.warning(f"Attempted to add task to unknown session {ip_address}")

    async def add_network_activity(self, ip_address: str, activity: str):
        """Log a network‑level activity for the given IP."""
        if ip_address in self.sessions:
            self.sessions[ip_address]["network_activity"].append(
                {"activity": activity, "timestamp": datetime.now()}
            )
            logger.info(f"Network activity added for {ip_address}: {activity}")
        else:
            logger.warning(f"Attempted to add network activity to unknown session {ip_address}")

    # ------------------------------------------------------------------
    # WebSocket real‑time updates
    # ------------------------------------------------------------------
    async def handle_websocket(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """
        Simple echo‑style WebSocket handler.
        Clients can send JSON messages:
        {
            "action": "add_task" | "add_network",
            "ip": "x.x.x.x",
            "payload": "string"
        }
        """
        logger.info(f"WebSocket connection opened from {websocket.remote_address}")
        try:
            async for raw_msg in websocket:
                try:
                    import json
                    msg = json.loads(raw_msg)
                    action = msg.get("action")
                    ip = msg.get("ip")
                    payload = msg.get("payload")

                    if action == "add_task":
                        await self.add_task(ip, payload)
                        await websocket.send(json.dumps({"status": "ok", "msg": "task added"}))
                    elif action == "add_network":
                        await self.add_network_activity(ip, payload)
                        await websocket.send(json.dumps({"status": "ok", "msg": "network activity added"}))
                    else:
                        await websocket.send(json.dumps({"status": "error", "msg": "unknown action"}))
                except Exception as e:
                    logger.exception("Error processing WebSocket message")
                    await websocket.send(json.dumps({"status": "error", "msg": str(e)}))
        finally:
            logger.info(f"WebSocket connection closed from {websocket.remote_address}")

    # ------------------------------------------------------------------
    # Dashboard (HTML template served via aiohttp)
    # ------------------------------------------------------------------
    async def start_dashboard(self, host: str = "0.0.0.0", port: int = 8080):
        """Launch a minimal aiohttp dashboard showing current sessions."""
        app = web.Application()
        app.router.add_get("/", self._dashboard_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Dashboard available at http://{host}:{port}")

    async def _dashboard_handler(self, request: web.Request):
        """Render a simple HTML page with session overview."""
        html = """
        <!doctype html>
        <html>
        <head>
            <title>LAN Session Dashboard</title>
            <style>
                body {font-family: Arial, sans-serif; margin: 20px;}
                table {border-collapse: collapse; width: 100%;}
                th, td {border: 1px solid #ddd; padding: 8px;}
                th {background-color: #f2f2f2;}
            </style>
        </head>
        <body>
            <h1>LAN Session Dashboard</h1>
            <table>
                <tr>
                    <th>IP Address</th>
                    <th>Created At</th>
                    <th>Timeout</th>
                    <th># Your Tasks</th>
                    <th># Network Activity</th>
                </tr>
                {rows}
            </table>
        </body>
        </html>
        """
        rows = ""
        for ip, data in self.sessions.items():
            timeout = data["timeout"].strftime("%Y-%m-%d %H:%M:%S") if data["timeout"] else "None"
            rows += f"""
            <tr>
                <td>{ip}</td>
                <td>{data["created_at"].strftime("%Y-%m-%d %H:%M:%S")}</td>
                <td>{timeout}</td>
                <td>{len(data["your_tasks"])}</td>
                <td>{len(data["network_activity"])}</td>
            </tr>
            """
        return web.Response(text=html.format(rows=rows), content_type="text/html")

# ----------------------------------------------------------------------
# Entry point for manual testing / development
# ----------------------------------------------------------------------
async def main():
    manager = SessionManager()

    # Start background session timeout monitor
    asyncio.create_task(manager.start())

    # Example: create a demo session (remove in production)
    await manager.create_session("192.168.0.42", timeout_seconds=300)

    # Launch WebSocket server (real‑time updates)
    ws_server = websockets.serve(manager.handle_websocket, "0.0.0.0", 8765)

    # Launch dashboard on port 8080
    await manager.start_dashboard(host="0.0.0.0", port=8080)

    # Run both servers concurrently
    await ws_server
    await asyncio.Future()  # keep the process alive

if __name__ == "__main__":
    asyncio.run(main())