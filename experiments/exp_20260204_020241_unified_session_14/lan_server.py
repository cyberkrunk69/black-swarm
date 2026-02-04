#!/usr/bin/env python3
"""
lan_server.py - Dual‑Server Infrastructure

Implements:
* AdminServer – binds only to 127.0.0.1 (local‑only)
* LANServer  – binds to 0.0.0.0 but accepts connections only from a
               configurable LAN CIDR (default 192.168.0.0/16)
* Request routing based on the client’s IP address
* Basic privilege‑level enforcement (admin vs. user)

The module can be used as a drop‑in replacement for the previous
`progress_server.py`.  It also provides small CLI helpers for quick
startup of each server.

Author: OpenAI ChatGPT
"""

import ipaddress
import threading
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs, urlparse

# ----------------------------------------------------------------------
# Configuration – adjust as needed
# ----------------------------------------------------------------------
LAN_CIDR = ipaddress.IPv4Network("192.168.0.0/16")  # allowed LAN range
ADMIN_BIND = "127.0.0.1"
LAN_BIND = "0.0.0.0"
DEFAULT_PORT = 8080

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def is_lan_address(addr: str) -> bool:
    """Return True if `addr` falls inside the configured LAN CIDR."""
    try:
        return ipaddress.IPv4Address(addr) in LAN_CIDR
    except ipaddress.AddressValueError:
        return False


def enforce_privilege(query: dict) -> str:
    """
    Very small privilege enforcement stub.
    Expected query param: `privilege=admin|user`
    Returns the privilege level (defaults to 'user').
    """
    priv = query.get("privilege", ["user"])[0]
    return priv if priv in ("admin", "user") else "user"


# ----------------------------------------------------------------------
# Core request handler – shared by both servers
# ----------------------------------------------------------------------
class DualRequestHandler(BaseHTTPRequestHandler):
    """
    Handles HTTP GET requests and dispatches them to the appropriate
    logic based on the client IP address and privilege level.
    """

    # Disable default logging (override to keep output clean)
    def log_message(self, format, *args):
        return

    def do_GET(self):
        client_ip = self.client_address[0]
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        privilege = enforce_privilege(query)

        # Routing decision
        if client_ip == "127.0.0.1":
            self.handle_admin_request(parsed.path, query, privilege)
        elif is_lan_address(client_ip):
            self.handle_lan_request(parsed.path, query, privilege)
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Forbidden: IP not allowed.\n")

    # ------------------------------------------------------------------
    # Admin request handling
    # ------------------------------------------------------------------
    def handle_admin_request(self, path: str, query: dict, privilege: str):
        """
        Admin‑only endpoints.  Only reachable from 127.0.0.1.
        """
        if privilege != "admin":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized: admin privilege required.\n")
            return

        if path == "/admin/status":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Admin Server: OK\n")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Admin endpoint not found.\n")

    # ------------------------------------------------------------------
    # LAN request handling
    # ------------------------------------------------------------------
    def handle_lan_request(self, path: str, query: dict, privilege: str):
        """
        LAN‑wide endpoints.  Accessible from any IP inside LAN_CIDR.
        """
        if path == "/lan/echo":
            message = query.get("msg", ["hello"])[0].encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Echo: " + message + b"\n")
        elif path == "/lan/status":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LAN Server: Running\n")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"LAN endpoint not found.\n")


# ----------------------------------------------------------------------
# Threaded HTTP server base class
# ----------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


# ----------------------------------------------------------------------
# Server classes
# ----------------------------------------------------------------------
class AdminServer:
    """
    Admin server bound to 127.0.0.1 only.
    """

    def __init__(self, port: int = DEFAULT_PORT):
        self.server_address = (ADMIN_BIND, port)
        self.httpd = ThreadedHTTPServer(self.server_address, DualRequestHandler)

    def start(self):
        print(f"[AdminServer] Listening on http://{ADMIN_BIND}:{self.server_address[1]}")
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        print("[AdminServer] Shutting down.")
        self.httpd.shutdown()


class LANServer:
    """
    LAN server bound to 0.0.0.0 but validates incoming client IPs.
    """

    def __init__(self, port: int = DEFAULT_PORT):
        self.server_address = (LAN_BIND, port)
        self.httpd = ThreadedHTTPServer(self.server_address, DualRequestHandler)

    def start(self):
        print(f"[LANServer] Listening on http://{LAN_BIND}:{self.server_address[1]}")
        print(f"[LANServer] Accepting connections from LAN CIDR: {LAN_CIDR}")
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        print("[LANServer] Shutting down.")
        self.httpd.shutdown()


# ----------------------------------------------------------------------
# CLI helpers – convenient entry points
# ----------------------------------------------------------------------
def _run_admin(port: int):
    server = AdminServer(port)
    server.start()


def _run_lan(port: int):
    server = LANServer(port)
    server.start()


def main():
    """
    Simple command‑line interface:

        python lan_server.py admin [port]
        python lan_server.py lan   [port]

    If no port is supplied, DEFAULT_PORT (8080) is used.
    """
    if len(sys.argv) < 2 or sys.argv[1] not in ("admin", "lan"):
        print("Usage: lan_server.py <admin|lan> [port]")
        sys.exit(1)

    role = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    if role == "admin":
        _run_admin(port)
    else:
        _run_lan(port)


if __name__ == "__main__":
    main()