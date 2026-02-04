"""
lan_server.py

Dual‑server implementation for the unified session experiment.

- AdminServer: listens only on 127.0.0.1 (loopback) and provides privileged endpoints.
- LANServer: listens on 0.0.0.0 (all interfaces) but only accepts requests originating from the
  local network (private IP ranges). It also offers a subset of endpoints that are safe for
  LAN users.

Both servers share a common request‑routing layer that inspects the client IP address
and dispatches to the appropriate Flask blueprint. Privilege enforcement is performed
via a simple token check for admin routes.

The module can be executed directly; it will spawn both servers in separate threads.
"""

import os
import threading
import ipaddress
from flask import Flask, request, jsonify, abort

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Simple shared secret for admin authentication (in a real system use a proper auth mechanism)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me-please")

# Private IP ranges considered "LAN". Adjust as needed.
LAN_SUBNETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def is_lan_ip(ip_str: str) -> bool:
    """Return True if the supplied IP address belongs to a LAN subnet."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in LAN_SUBNETS)
    except ValueError:
        return False


def get_remote_ip() -> str:
    """Extract the remote IP address from the Flask request."""
    # Flask may report the proxy address; for simplicity we trust X-Forwarded-For if present.
    if "X-Forwarded-For" in request.headers:
        # X-Forwarded-For can contain a list; take the first entry.
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or ""


def admin_required(fn):
    """Decorator that enforces the presence of a valid admin token."""
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if token != ADMIN_TOKEN:
            abort(403, description="Admin token missing or invalid")
        return fn(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Flask app factories
# ---------------------------------------------------------------------------


def create_admin_app() -> Flask:
    """Flask app bound to 127.0.0.1 – exposes privileged endpoints."""
    app = Flask("AdminServer")

    @app.route("/admin/status")
    @admin_required
    def admin_status():
        return jsonify({"status": "admin server alive", "origin": get_remote_ip()})

    @app.route("/admin/shutdown", methods=["POST"])
    @admin_required
    def admin_shutdown():
        """Graceful shutdown of the admin server (used only for testing)."""
        func = request.environ.get("werkzeug.server.shutdown")
        if func is None:
            abort(500, description="Not running with the Werkzeug Server")
        func()
        return jsonify({"msg": "admin server shutting down"})

    # Example privileged operation
    @app.route("/admin/echo", methods=["POST"])
    @admin_required
    def admin_echo():
        data = request.get_json(silent=True) or {}
        return jsonify({"echo": data, "origin": get_remote_ip()})

    return app


def create_lan_app() -> Flask:
    """Flask app bound to 0.0.0.0 – serves LAN‑only endpoints."""
    app = Flask("LANServer")

    @app.before_request
    def restrict_to_lan():
        remote_ip = get_remote_ip()
        if not is_lan_ip(remote_ip):
            abort(403, description="Access restricted to LAN clients")

    @app.route("/lan/ping")
    def lan_ping():
        return jsonify({"msg": "pong", "origin": get_remote_ip()})

    @app.route("/lan/info")
    def lan_info():
        # Return a non‑sensitive snapshot of server state
        return jsonify(
            {
                "server": "LANServer",
                "lan_subnets": [str(net) for net in LAN_SUBNETS],
                "origin": get_remote_ip(),
            }
        )

    # Example public endpoint that does not require admin rights
    @app.route("/lan/echo", methods=["POST"])
    def lan_echo():
        data = request.get_json(silent=True) or {}
        return jsonify({"echo": data, "origin": get_remote_ip()})

    return app


# ---------------------------------------------------------------------------
# Server runner utilities
# ---------------------------------------------------------------------------


def run_admin_server(host="127.0.0.1", port=5001):
    """Start the AdminServer."""
    app = create_admin_app()
    # Using threaded=True to allow concurrent handling while the LAN server runs.
    app.run(host=host, port=port, threaded=True)


def run_lan_server(host="0.0.0.0", port=5000):
    """Start the LANServer."""
    app = create_lan_app()
    app.run(host=host, port=port, threaded=True)


def start_dual_servers():
    """Spawn AdminServer and LANServer in separate daemon threads."""
    admin_thread = threading.Thread(
        target=run_admin_server, name="AdminServerThread", daemon=True
    )
    lan_thread = threading.Thread(
        target=run_lan_server, name="LANServerThread", daemon=True
    )
    admin_thread.start()
    lan_thread.start()
    # Keep the main thread alive while child threads run.
    admin_thread.join()
    lan_thread.join()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    When executed directly, the module launches both servers.
    The admin server is intentionally bound to the loopback interface,
    while the LAN server listens on all interfaces but validates the client
    IP against private LAN ranges.
    """
    start_dual_servers()