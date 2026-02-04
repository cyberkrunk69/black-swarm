"""
lan_server.py
Dual‑Server Infrastructure

Provides:
- AdminServer : bound to 127.0.0.1 (localhost only)
- LANServer  : bound to 0.0.0.0 (all interfaces) but only accepts requests from
               the local network (private IPv4 ranges) and enforces a simple
               privilege model.

The module can be used as a drop‑in replacement for ``progress_server.py`` – it
exposes the same Flask ``app`` objects so existing import paths continue to work.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Callable, Dict

from flask import Flask, request, jsonify, abort

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def ip_in_private_range(ip: str) -> bool:
    """Return True if *ip* belongs to a private IPv4 network."""
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


def get_client_ip() -> str:
    """Extract the most reliable client IP from the Flask request."""
    # Flask may be behind a proxy – respect the X-Forwarded-For header if present.
    if "X-Forwarded-For" in request.headers:
        # X-Forwarded-For may contain a list, the left‑most is the original client.
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr or ""


def require_privilege(level: int) -> Callable:
    """
    Decorator that aborts the request if the ``X-Privilege`` header is lower than
    *level*.  Privilege levels:
        0 – guest / read‑only
        1 – normal user
        2 – admin
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                client_level = int(request.headers.get("X-Privilege", "0"))
            except ValueError:
                client_level = 0
            if client_level < level:
                abort(403, description="Insufficient privilege")
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


# --------------------------------------------------------------------------- #
# Admin Server (localhost only)
# --------------------------------------------------------------------------- #
admin_app = Flask("admin_server")

@admin_app.route("/admin/status")
@require_privilege(2)
def admin_status():
    """Return a simple status payload for the admin interface."""
    return jsonify({
        "server": "admin",
        "status": "online",
        "pid": os.getpid()
    })


@admin_app.route("/admin/echo", methods=["POST"])
@require_privilege(2)
def admin_echo():
    """Echo back JSON payload – useful for quick health‑checks."""
    return jsonify(request.get_json(silent=True) or {})


def run_admin_server(host: str = "127.0.0.1", port: int = 5000):
    """Entry‑point for the admin server."""
    admin_app.run(host=host, port=port, debug=False)


# --------------------------------------------------------------------------- #
# LAN Server (public on LAN, restricted)
# --------------------------------------------------------------------------- #
lan_app = Flask("lan_server")

# Example in‑memory data store – replace with real persistence as needed.
_DATA_STORE: Dict[str, str] = {"example": "value"}

@lan_app.before_request
def restrict_to_private_network():
    """Reject any request that does not originate from a private IPv4 address."""
    client_ip = get_client_ip()
    if not ip_in_private_range(client_ip):
        abort(403, description="Access denied: non‑LAN source")


@lan_app.route("/lan/ping")
def lan_ping():
    """Simple health‑check endpoint reachable from any LAN client."""
    return jsonify({"msg": "pong", "client_ip": get_client_ip()})


@lan_app.route("/lan/data/<key>", methods=["GET"])
@require_privilege(0)  # read‑only access
def lan_get_data(key: str):
    """Retrieve a value from the in‑memory store."""
    if key not in _DATA_STORE:
        abort(404, description="Key not found")
    return jsonify({key: _DATA_STORE[key]})


@lan_app.route("/lan/data/<key>", methods=["POST"])
@require_privilege(1)  # requires at least normal user
def lan_set_data(key: str):
    """Create / update a value in the in‑memory store."""
    payload = request.get_json(silent=True)
    if not payload or "value" not in payload:
        abort(400, description="Missing 'value' in JSON body")
    _DATA_STORE[key] = payload["value"]
    return jsonify({"msg": "updated", key: _DATA_STORE[key]}), 201


def run_lan_server(host: str = "0.0.0.0", port: int = 5001):
    """Entry‑point for the LAN server."""
    lan_app.run(host=host, port=port, debug=False)


# --------------------------------------------------------------------------- #
# Unified dispatcher (optional convenience)
# --------------------------------------------------------------------------- #
def dispatch_request():
    """
    Helper that can be used by a single Flask instance to forward requests to
    the appropriate sub‑application based on the client IP.
    """
    client_ip = get_client_ip()
    if client_ip == "127.0.0.1":
        return admin_app.full_dispatch_request()
    else:
        return lan_app.full_dispatch_request()


# --------------------------------------------------------------------------- #
# When executed directly, start both servers in separate processes.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import multiprocessing

    admin_proc = multiprocessing.Process(target=run_admin_server, args=("127.0.0.1", 5000))
    lan_proc = multiprocessing.Process(target=run_lan_server, args=("0.0.0.0", 5001))

    admin_proc.start()
    lan_proc.start()

    admin_proc.join()
    lan_proc.join()