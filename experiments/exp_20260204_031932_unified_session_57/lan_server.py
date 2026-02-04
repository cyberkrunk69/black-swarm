#!/usr/bin/env python3
"""
lan_server.py - Dual‑server infrastructure.

Implements:
* AdminServer – binds to 127.0.0.1 only, serves privileged admin endpoints.
* LANServer  – binds to 0.0.0.0, serves LAN‑wide endpoints but restricts access to
               trusted sub‑nets and enforces privilege levels.

Both servers are started in separate threads when the module is executed directly.
"""

import threading
import ipaddress
import logging
from flask import Flask, request, jsonify, abort

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Admin server: only localhost may connect
ADMIN_HOST = "127.0.0.1"
ADMIN_PORT = 5001

# LAN server: listen on all interfaces, but only allow trusted LAN ranges
LAN_HOST = "0.0.0.0"
LAN_PORT = 5000
TRUSTED_SUBNETS = [
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
]

# Logging
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def ip_in_trusted_subnet(ip_str: str) -> bool:
    """Return True if the given IP address string belongs to any trusted subnet."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in net for net in TRUSTED_SUBNETS)
    except ValueError:
        return False

def get_remote_ip() -> str:
    """Extract the remote IP from Flask request (handles proxies)."""
    # Flask's request.remote_addr respects the direct socket connection.
    # If the deployment sits behind a reverse proxy, you may need to inspect
    # X-Forwarded-For. For this simple implementation we trust remote_addr.
    return request.remote_addr or "0.0.0.0"

# --------------------------------------------------------------------------- #
# Admin Server
# --------------------------------------------------------------------------- #

admin_app = Flask("AdminServer")

@admin_app.before_request
def enforce_admin_origin():
    """Only allow connections originating from 127.0.0.1."""
    remote_ip = get_remote_ip()
    if remote_ip != "127.0.0.1":
        logging.warning("Blocked admin request from %s", remote_ip)
        abort(403, description="Admin interface is localhost‑only.")

@admin_app.route("/admin/status", methods=["GET"])
def admin_status():
    """Simple health‑check endpoint for admin use."""
    return jsonify({
        "service": "AdminServer",
        "status": "ok",
        "origin": get_remote_ip()
    })

@admin_app.route("/admin/shutdown", methods=["POST"])
def admin_shutdown():
    """Endpoint to gracefully shut down the admin server (admin‑only)."""
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        abort(500, description="Not running with the Werkzeug Server")
    logging.info("Admin requested shutdown.")
    func()
    return jsonify({"message": "Admin server shutting down"}), 200

def run_admin_server():
    logging.info("Starting AdminServer on %s:%s", ADMIN_HOST, ADMIN_PORT)
    admin_app.run(host=ADMIN_HOST, port=ADMIN_PORT, debug=False, use_reloader=False)

# --------------------------------------------------------------------------- #
# LAN Server
# --------------------------------------------------------------------------- #

lan_app = Flask("LANServer")

@lan_app.before_request
def enforce_lan_origin():
    """Allow only requests from trusted LAN subnets."""
    remote_ip = get_remote_ip()
    if not ip_in_trusted_subnet(remote_ip):
        logging.warning("Blocked LAN request from %s (outside trusted subnets)", remote_ip)
        abort(403, description="Access denied: IP not in trusted LAN range.")

@lan_app.route("/lan/ping", methods=["GET"])
def lan_ping():
    """Public ping endpoint – reachable only from trusted LAN."""
    return jsonify({
        "service": "LANServer",
        "message": "pong",
        "origin": get_remote_ip()
    })

@lan_app.route("/lan/data", methods=["POST"])
def lan_data():
    """
    Example privileged endpoint.
    In a real system you would extract user credentials / tokens and
    verify privilege levels here.
    """
    payload = request.get_json(silent=True) or {}
    # Placeholder privilege check – extend as needed.
    if not payload.get("privileged"):
        logging.info("Non‑privileged request from %s rejected", get_remote_ip())
        abort(403, description="Insufficient privileges.")
    logging.info("Privileged data received from %s", get_remote_ip())
    return jsonify({"status": "accepted", "received": payload}), 200

def run_lan_server():
    logging.info("Starting LANServer on %s:%s", LAN_HOST, LAN_PORT)
    lan_app.run(host=LAN_HOST, port=LAN_PORT, debug=False, use_reloader=False)

# --------------------------------------------------------------------------- #
# Main entry point – start both servers in parallel threads
# --------------------------------------------------------------------------- #

def start_dual_servers():
    """Launch AdminServer and LANServer concurrently."""
    admin_thread = threading.Thread(target=run_admin_server, daemon=True, name="AdminServerThread")
    lan_thread = threading.Thread(target=run_lan_server, daemon=True, name="LANServerThread")

    admin_thread.start()
    lan_thread.start()

    logging.info("Both servers are up. Press Ctrl+C to terminate.")
    try:
        # Keep the main thread alive while child threads run.
        while admin_thread.is_alive() and lan_thread.is_alive():
            admin_thread.join(timeout=1.0)
            lan_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Exiting...")

if __name__ == "__main__":
    start_dual_servers()