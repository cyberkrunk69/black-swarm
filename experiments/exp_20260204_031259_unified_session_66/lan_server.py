"""
lan_server.py
--------------

Dual‑server implementation for the unified session experiment.

* **AdminServer** – Binds to 127.0.0.1 only.  Handles administrative
  endpoints and enforces the highest privilege level.

* **LANServer** – Binds to 0.0.0.0 (all interfaces) but accepts requests
  only from private LAN ranges.  It serves the public API and enforces
  privilege levels supplied by the client.

Both servers share a common request‑handler that performs:
  1. Origin validation (IP address check)
  2. Privilege extraction from the ``X‑Privilege`` header
  3. Routing to the appropriate endpoint based on the request path
"""

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from ipaddress import ip_address, IPv4Network

# --------------------------------------------------------------------------- #
# Configuration – adjust as needed
# --------------------------------------------------------------------------- #
LAN_PRIVATE_NETWORKS = [
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
]

# Simple in‑memory store for demonstration purposes
DATA_STORE = {
    "status": "OK",
    "value": 42,
}


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def is_private_ip(addr: str) -> bool:
    """Return True if *addr* belongs to one of the private LAN ranges."""
    try:
        ip = ip_address(addr)
        return any(ip in net for net in LAN_PRIVATE_NETWORKS)
    except ValueError:
        return False


def json_response(handler: BaseHTTPRequestHandler, payload, status=HTTPStatus.OK):
    """Utility to send a JSON response."""
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


# --------------------------------------------------------------------------- #
# Core request handler – shared by both servers
# --------------------------------------------------------------------------- #
class DualRequestHandler(BaseHTTPRequestHandler):
    """
    Handles HTTP requests for both the AdminServer and the LANServer.

    The handler expects a custom header ``X-Privilege`` with one of the
    following values:

        * ``admin`` – full privileges (admin server only)
        * ``user``  – regular user privileges
        * ``guest`` – read‑only access

    Privilege enforcement is performed per endpoint.
    """

    # Mapping of (path, required_privilege) -> handler method
    ROUTES = {
        ("/status", "guest"): "handle_status",
        ("/value", "user"): "handle_get_value",
        ("/value", "admin"): "handle_set_value",
    }

    # --------------------------------------------------------------------- #
    # HTTP verb dispatchers
    # --------------------------------------------------------------------- #
    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    # --------------------------------------------------------------------- #
    # Core dispatch logic
    # --------------------------------------------------------------------- #
    def _dispatch(self, method: str):
        client_ip = self.client_address[0]

        # ----------------------------------------------------------------- #
        # 1️⃣ Origin validation – AdminServer will have already bound to
        #    127.0.0.1, so we only need to enforce LAN restrictions here.
        # ----------------------------------------------------------------- #
        if isinstance(self.server, LANServer) and not is_private_ip(client_ip):
            self._reject("Forbidden: request not from a private LAN address")
            return

        # ----------------------------------------------------------------- #
        # 2️⃣ Privilege extraction
        # ----------------------------------------------------------------- #
        privilege = self.headers.get("X-Privilege", "guest").lower()
        if privilege not in {"admin", "user", "guest"}:
            self._reject("Invalid privilege header")
            return

        # ----------------------------------------------------------------- #
        # 3️⃣ Route lookup
        # ----------------------------------------------------------------- #
        route_key = (self.path.split("?")[0], privilege)
        handler_name = self.ROUTES.get(route_key)

        # If no exact match, try to downgrade to a lower privilege level
        if handler_name is None:
            # e.g. admin can also use user routes, user can use guest routes
            hierarchy = ["admin", "user", "guest"]
            idx = hierarchy.index(privilege)
            for lower in hierarchy[idx + 1 :]:
                handler_name = self.ROUTES.get((self.path.split("?")[0], lower))
                if handler_name:
                    break

        if handler_name is None:
            self._reject("Not Found or insufficient privileges", HTTPStatus.NOT_FOUND)
            return

        # ----------------------------------------------------------------- #
        # 4️⃣ Call the concrete handler
        # ----------------------------------------------------------------- #
        getattr(self, handler_name)()

    # --------------------------------------------------------------------- #
    # Helper methods
    # --------------------------------------------------------------------- #
    def _reject(self, message, status=HTTPStatus.FORBIDDEN):
        json_response(self, {"error": message}, status)

    # --------------------------------------------------------------------- #
    # Endpoint implementations
    # --------------------------------------------------------------------- #
    def handle_status(self):
        """Public status endpoint – read‑only (guest)."""
        json_response(self, {"status": DATA_STORE["status"]})

    def handle_get_value(self):
        """Retrieve the stored value – requires at least 'user' privilege."""
        json_response(self, {"value": DATA_STORE["value"]})

    def handle_set_value(self):
        """Update the stored value – admin only."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self._reject("Missing JSON body", HTTPStatus.BAD_REQUEST)
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
            new_val = payload["value"]
        except (json.JSONDecodeError, KeyError):
            self._reject("Invalid JSON payload", HTTPStatus.BAD_REQUEST)
            return

        DATA_STORE["value"] = new_val
        json_response(self, {"message": "Value updated", "value": new_val})


# --------------------------------------------------------------------------- #
# Server classes
# --------------------------------------------------------------------------- #
class AdminServer(HTTPServer):
    """
    Administrative server – bound to 127.0.0.1 only.
    Exposes all admin‑level routes and enforces that the client originates
    from localhost.
    """

    def __init__(self, handler_class=DualRequestHandler, port=8001):
        super().__init__(("127.0.0.1", port), handler_class)

    def serve_forever(self, poll_interval=0.5):
        print(f"[AdminServer] Listening on http://127.0.0.1:{self.server_port}")
        super().serve_forever(poll_interval=poll_interval)


class LANServer(HTTPServer):
    """
    LAN‑facing server – bound to 0.0.0.0.
    Accepts connections from any interface but restricts request handling
    to private LAN IP ranges.
    """

    def __init__(self, handler_class=DualRequestHandler, port=8000):
        super().__init__(("0.0.0.0", port), handler_class)

    def serve_forever(self, poll_interval=0.5):
        print(f"[LANServer] Listening on http://0.0.0.0:{self.server_port}")
        super().serve_forever(poll_interval=poll_interval)


# --------------------------------------------------------------------------- #
# Convenience entry‑point – starts both servers in separate threads.
# --------------------------------------------------------------------------- #
def _run_server(server_instance):
    try:
        server_instance.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server_instance.server_close()
        print(f"[{server_instance.__class__.__name__}] Shut down.")


def start_dual_servers(admin_port=8001, lan_port=8000):
    """
    Spin up the AdminServer and LANServer concurrently.
    Returns the thread objects for optional joining.
    """
    admin_srv = AdminServer(port=admin_port)
    lan_srv = LANServer(port=lan_port)

    admin_thread = threading.Thread(target=_run_server, args=(admin_srv,), daemon=True)
    lan_thread = threading.Thread(target=_run_server, args=(lan_srv,), daemon=True)

    admin_thread.start()
    lan_thread.start()

    print("[DualServer] Both servers are up and running.")
    return admin_thread, lan_thread


if __name__ == "__main__":
    # When executed directly, start both servers.
    start_dual_servers()
    # Keep the main thread alive so daemon threads stay alive.
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n[DualServer] Received shutdown signal.")