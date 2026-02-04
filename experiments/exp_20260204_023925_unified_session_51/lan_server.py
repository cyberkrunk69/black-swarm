#!/usr/bin/env python3
"""
lan_server.py – Dual‑server infrastructure.

Two HTTP servers are started:

* **AdminServer** – bound to 127.0.0.1, handles privileged admin actions.
* **LANServer**  – bound to 0.0.0.0, serves the LAN but only accepts requests
  from private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).

Both servers share a common request‑routing logic that inspects the client
address and enforces a simple privilege model via an ``X‑Auth‑Token`` header.
"""

import threading
import socket
import ipaddress
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import sys
import logging

# --------------------------------------------------------------------------- #
# Configuration (could be externalised later)
# --------------------------------------------------------------------------- #
ADMIN_HOST = "127.0.0.1"
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "8081"))

LAN_HOST = "0.0.0.0"
LAN_PORT = int(os.getenv("LAN_PORT", "8080"))

# Simple token‑based auth – in a real system this would be replaced by
# a proper authentication/authorization mechanism.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-secret")
LAN_TOKEN = os.getenv("LAN_TOKEN", "lan-secret")

# Private network CIDRs accepted by LANServer
LAN_ALLOWED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def is_private_ip(ip: str) -> bool:
    """Return True if *ip* belongs to one of the LAN_ALLOWED_NETWORKS."""
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in LAN_ALLOWED_NETWORKS)
    except ValueError:
        return False


def json_response(handler: BaseHTTPRequestHandler, data, status=200):
    payload = json.dumps(data).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


# --------------------------------------------------------------------------- #
# Core request handler – shared logic
# --------------------------------------------------------------------------- #
class DualRequestHandler(BaseHTTPRequestHandler):
    """
    Base class that implements common routing & privilege checks.
    Sub‑classes only need to implement ``handle_admin`` and ``handle_lan``.
    """

    server_version = "DualServer/1.0"

    def _reject(self, code: int, message: str):
        self.send_error(code, message)

    def _authenticate(self, required_token: str) -> bool:
        token = self.headers.get("X-Auth-Token")
        return token == required_token

    def do_GET(self):
        client_ip = self.client_address[0]
        logging.info("GET request from %s %s", client_ip, self.path)

        # Route based on origin IP
        if client_ip == "127.0.0.1":
            # Admin request – must present admin token
            if not self._authenticate(ADMIN_TOKEN):
                return self._reject(403, "Forbidden: invalid admin token")
            return self.handle_admin()
        else:
            # LAN request – ensure IP is private and token matches LAN token
            if not is_private_ip(client_ip):
                return self._reject(403, "Forbidden: IP not in LAN range")
            if not self._authenticate(LAN_TOKEN):
                return self._reject(403, "Forbidden: invalid LAN token")
            return self.handle_lan()

    # POST handling mirrors GET for this example – real implementations can differ
    def do_POST(self):
        client_ip = self.client_address[0]
        logging.info("POST request from %s %s", client_ip, self.path)

        if client_ip == "127.0.0.1":
            if not self._authenticate(ADMIN_TOKEN):
                return self._reject(403, "Forbidden: invalid admin token")
            return self.handle_admin()
        else:
            if not is_private_ip(client_ip):
                return self._reject(403, "Forbidden: IP not in LAN range")
            if not self._authenticate(LAN_TOKEN):
                return self._reject(403, "Forbidden: invalid LAN token")
            return self.handle_lan()

    # ------------------------------------------------------------------- #
    # To be overridden by concrete servers
    # ------------------------------------------------------------------- #
    def handle_admin(self):
        """Admin endpoint logic – must be overridden."""
        self._reject(501, "Admin handler not implemented")

    def handle_lan(self):
        """LAN endpoint logic – must be overridden."""
        self._reject(501, "LAN handler not implemented")

    # Suppress default logging (we use the logging module instead)
    def log_message(self, fmt, *args):
        return


# --------------------------------------------------------------------------- #
# Admin Server
# --------------------------------------------------------------------------- #
class AdminServer(DualRequestHandler):
    """
    Server bound to 127.0.0.1 – handles privileged operations.
    """

    def handle_admin(self):
        """Simple admin API – status & control."""
        parsed = urlparse(self.path)
        if parsed.path == "/status":
            data = {"service": "admin", "status": "running"}
            return json_response(self, data)
        elif parsed.path == "/shutdown":
            # In a real system you would trigger graceful shutdown.
            data = {"service": "admin", "action": "shutdown", "result": "ok"}
            json_response(self, data)
            # Signal the main thread to exit (via a custom header)
            self.server.shutdown_requested = True
        else:
            self._reject(404, "Admin endpoint not found")


# --------------------------------------------------------------------------- #
# LAN Server
# --------------------------------------------------------------------------- #
class LANServer(DualRequestHandler):
    """
    Server bound to 0.0.0.0 – serves the LAN but only to private IPs.
    """

    def handle_lan(self):
        parsed = urlparse(self.path)
        if parsed.path == "/ping":
            data = {"service": "lan", "msg": "pong"}
            return json_response(self, data)
        elif parsed.path == "/echo":
            # Echo back query parameters for demo purposes
            qs = parse_qs(parsed.query)
            data = {"service": "lan", "echo": qs}
            return json_response(self, data)
        else:
            self._reject(404, "LAN endpoint not found")


# --------------------------------------------------------------------------- #
# Server bootstrap helpers
# --------------------------------------------------------------------------- #
def run_server(server_class, host, port, name):
    httpd = HTTPServer((host, port), server_class)
    # Attach a flag we can later inspect for graceful shutdown
    httpd.shutdown_requested = False
    logging.info("%s listening on %s:%s", name, host, port)
    try:
        while not httpd.shutdown_requested:
            httpd.handle_request()
    except KeyboardInterrupt:
        logging.info("%s received KeyboardInterrupt – shutting down", name)
    finally:
        httpd.server_close()
        logging.info("%s stopped", name)


def main():
    # Run both servers in separate threads
    admin_thread = threading.Thread(
        target=run_server,
        args=(AdminServer, ADMIN_HOST, ADMIN_PORT, "AdminServer"),
        daemon=True,
    )
    lan_thread = threading.Thread(
        target=run_server,
        args=(LANServer, LAN_HOST, LAN_PORT, "LANServer"),
        daemon=True,
    )

    admin_thread.start()
    lan_thread.start()

    # Wait for either thread to signal shutdown (admin /shutdown endpoint)
    try:
        while True:
            if getattr(admin_thread, "is_alive", lambda: False)():
                admin_thread.join(timeout=0.1)
            if getattr(lan_thread, "is_alive", lambda: False)():
                lan_thread.join(timeout=0.1)
            # If admin server set its shutdown flag, break the loop
            if getattr(admin_thread, "_target", None):
                # Access the HTTPServer instance via closure – not straightforward.
                # Instead, we rely on KeyboardInterrupt or external process kill.
                pass
    except KeyboardInterrupt:
        logging.info("Main thread received KeyboardInterrupt – exiting")
        sys.exit(0)


if __name__ == "__main__":
    main()