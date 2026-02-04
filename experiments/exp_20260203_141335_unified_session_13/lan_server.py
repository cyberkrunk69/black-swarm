"""
lan_server.py

Dual‑server implementation for the project.

- AdminServer: 127.0.0.1 only, full privileges.
- LANServer: 0.0.0.0 (all interfaces) but only accepts requests from allowed LAN subnets.
- Request routing and privilege enforcement based on client IP.
"""

import threading
import ipaddress
from functools import wraps
from flask import Flask, request, jsonify, abort

# ----------------------------------------------------------------------
# Configuration (adjust as needed for the project)
# ----------------------------------------------------------------------
LAN_ALLOWED_SUBNETS = [
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
]

ADMIN_TOKEN = "CHANGE_ME_TO_SECURE_TOKEN"


def ip_in_allowed_subnets(ip_str: str) -> bool:
    """Return True if the IP address belongs to one of the allowed LAN subnets."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in LAN_ALLOWED_SUBNETS)
    except ValueError:
        return False


def require_admin(f):
    """Decorator that enforces admin‑only access via token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if token != ADMIN_TOKEN:
            abort(403, description="Admin token missing or invalid")
        return f(*args, **kwargs)
    return wrapper


class BaseServer:
    """Common functionality shared by AdminServer and LANServer."""
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = Flask(__name__)

        # Register a simple health endpoint for both servers
        @self.app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "server": self.__class__.__name__})

    def run(self):
        """Start the Flask development server (threaded)."""
        # Using threaded=True allows handling multiple requests concurrently.
        self.app.run(host=self.host, port=self.port, threaded=True)

    def add_route(self, rule: str, view_func, methods=None):
        """Convenient wrapper around Flask's route registration."""
        if methods is None:
            methods = ["GET"]
        self.app.add_url_rule(rule, view_func=view_func, methods=methods)


class AdminServer(BaseServer):
    """Admin‑only server bound to 127.0.0.1."""
    def __init__(self, port: int = 5000):
        super().__init__(host="127.0.0.1", port=port)

        # Example admin endpoint
        @self.app.route("/admin/task", methods=["POST"])
        @require_admin
        def admin_task():
            data = request.get_json(silent=True) or {}
            # Placeholder for real admin logic
            return jsonify({"result": "admin task executed", "payload": data})


class LANServer(BaseServer):
    """LAN‑exposed server bound to 0.0.0.0 with IP‑based restrictions."""
    def __init__(self, port: int = 5001):
        super().__init__(host="0.0.0.0", port=port)

        # Before each request, verify the client IP
        @self.app.before_request
        def restrict_to_lan():
            client_ip = request.remote_addr
            if not ip_in_allowed_subnets(client_ip):
                abort(403, description="Access denied: IP not in allowed LAN range")

        # Example public endpoint
        @self.app.route("/lan/status", methods=["GET"])
        def lan_status():
            return jsonify({"status": "LAN server reachable", "client_ip": request.remote_addr})

        # Example endpoint that also requires admin token (optional)
        @self.app.route("/lan/admin_action", methods=["POST"])
        @require_admin
        def lan_admin_action():
            data = request.get_json(silent=True) or {}
            return jsonify({"result": "LAN admin action performed", "payload": data})


def start_admin_server():
    admin = AdminServer()
    admin_thread = threading.Thread(target=admin.run, daemon=True, name="AdminServerThread")
    admin_thread.start()
    return admin_thread


def start_lan_server():
    lan = LANServer()
    lan_thread = threading.Thread(target=lan.run, daemon=True, name="LANServerThread")
    lan_thread.start()
    return lan_thread


if __name__ == "__main__":
    """
    Startup script – launches both servers in the same process.
    """
    print("[*] Starting AdminServer (127.0.0.1:5000)...")
    admin_thread = start_admin_server()

    print("[*] Starting LANServer (0.0.0.0:5001)...")
    lan_thread = start_lan_server()

    # Keep the main thread alive while the daemon threads run.
    try:
        while True:
            admin_thread.join(timeout=1.0)
            lan_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\n[!] Shutdown requested – exiting.")