#!/usr/bin/env python3
"""
lan_server.py – Dual‑server implementation.

Two HTTP servers are launched:

* **AdminServer** – binds to 127.0.0.1:8000 and only accepts requests from the
  local machine.  It is intended for privileged operations.

* **LANServer** – binds to 0.0.0.0:8001 and accepts requests from the private
  LAN (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).  It serves the regular
  (non‑admin) API.

Both servers share the same request‑handling logic; the only difference is the
origin‑based access control and the privilege level that is injected into the
handler.

The file can be started directly:

    python lan_server.py admin   # start AdminServer
    python lan_server.py lan     # start LANServer

or both can be launched via the provided batch scripts in the same folder.
"""

import sys
import ipaddress
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socket import gethostname, gethostbyname_ex

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def is_private_ip(ip: str) -> bool:
    """Return True if *ip* belongs to a typical private LAN range."""
    try:
        addr = ipaddress.ip_address(ip)
        return (
            addr.is_private
            and not addr.is_loopback
        )
    except ValueError:
        return False


def client_ip_address(handler: BaseHTTPRequestHandler) -> str:
    """Extract the remote IP address from the handler."""
    return handler.client_address[0]


# --------------------------------------------------------------------------- #
# Core request handler (shared by both servers)
# --------------------------------------------------------------------------- #

class DualRequestHandler(BaseHTTPRequestHandler):
    """
    Handles GET/POST requests and enforces privilege level.

    The handler expects the server instance to expose a ``privilege`` attribute
    (either ``'admin'`` or ``'user'``).  The attribute is injected by the
    server factory below.
    """

    server_version = "DualServer/1.0"

    def _log(self, message: str):
        """Simple stdout logging with server name."""
        sys.stdout.write(f"[{self.server.privilege.upper()}] {message}\n")

    def do_GET(self):
        client_ip = client_ip_address(self)
        self._log(f"Received GET from {client_ip} – Path: {self.path}")

        # Simple routing based on privilege
        if self.server.privilege == "admin":
            self.handle_admin_get()
        else:
            self.handle_user_get()

    def do_POST(self):
        client_ip = client_ip_address(self)
        self._log(f"Received POST from {client_ip} – Path: {self.path}")

        if self.server.privilege == "admin":
            self.handle_admin_post()
        else:
            self.handle_user_post()

    # ------------------------------------------------------------------- #
    # Admin‑specific handlers
    # ------------------------------------------------------------------- #
    def handle_admin_get(self):
        # Example: expose internal diagnostics
        content = ("<h1>Admin Dashboard</h1>"
                   "<p>Server hostname: {}</p>"
                   "<p>Client IP: {}</p>").format(
            gethostname(), client_ip_address(self))
        self._respond(200, content.encode("utf-8"))

    def handle_admin_post(self):
        # Echo back posted data (for demo purposes)
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length) if length else b''
        response = f"Admin POST received ({len(data)} bytes).".encode()
        self._respond(200, response)

    # ------------------------------------------------------------------- #
    # User (LAN) handlers
    # ------------------------------------------------------------------- #
    def handle_user_get(self):
        # Simple public endpoint
        content = ("<h1>LAN Service</h1>"
                   "<p>Welcome, client {}</p>").format(client_ip_address(self))
        self._respond(200, content.encode("utf-8"))

    def handle_user_post(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length) if length else b''
        response = f"LAN POST received ({len(data)} bytes).".encode()
        self._respond(200, response)

    # ------------------------------------------------------------------- #
    # Utility response method
    # ------------------------------------------------------------------- #
    def _respond(self, code: int, body: bytes, content_type: str = "text/html"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Suppress default logging (we use our own)
    def log_message(self, format, *args):
        return


# --------------------------------------------------------------------------- #
# Server factories
# --------------------------------------------------------------------------- #

def make_admin_server(host: str = "127.0.0.1", port: int = 8000) -> HTTPServer:
    """Create a server that only accepts connections from localhost."""
    server = HTTPServer((host, port), DualRequestHandler)
    server.privilege = "admin"
    return server


def make_lan_server(host: str = "0.0.0.0", port: int = 8001) -> HTTPServer:
    """
    Create a LAN‑exposed server.

    The server will reject any request whose remote address is not in a private
    LAN range.  The check happens in the request handler's ``setup`` method.
    """
    class LANRestrictedHandler(DualRequestHandler):
        def setup(self):
            super().setup()
            client_ip = client_ip_address(self)
            if not is_private_ip(client_ip):
                # Immediate denial – we close the connection.
                self._log(f"Blocked non‑LAN request from {client_ip}")
                self.send_error(403, "Forbidden: non‑LAN address")
                # Close the connection early
                self.finish()
                raise ConnectionResetError("Non‑LAN client")

    server = HTTPServer((host, port), LANRestrictedHandler)
    server.privilege = "user"
    return server


# --------------------------------------------------------------------------- #
# Thread runner utilities
# --------------------------------------------------------------------------- #

def run_server(server: HTTPServer):
    """Run the supplied HTTPServer in the current thread."""
    host, port = server.server_address
    print(f"[{server.privilege.upper()}] Starting on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{server.privilege.upper()}] Shutting down.")
    finally:
        server.server_close()


def start_threaded(server: HTTPServer):
    """Start the server in a daemon thread and return the thread object."""
    thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    thread.start()
    return thread


# --------------------------------------------------------------------------- #
# Main entry point – command line interface
# --------------------------------------------------------------------------- #

def print_usage():
    sys.stdout.write(
        "Usage: python lan_server.py [admin|lan|both]\n"
        "  admin – start only the AdminServer (127.0.0.1:8000)\n"
        "  lan   – start only the LANServer (0.0.0.0:8001, LAN‑restricted)\n"
        "  both  – start both servers concurrently (default)\n"
    )


def main():
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "both"

    if mode not in ("admin", "lan", "both"):
        print_usage()
        sys.exit(1)

    threads = []

    if mode in ("admin", "both"):
        admin_srv = make_admin_server()
        threads.append(start_threaded(admin_srv))

    if mode in ("lan", "both"):
        lan_srv = make_lan_server()
        threads.append(start_threaded(lan_srv))

    # Keep the main thread alive while child threads run
    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.5)
    except KeyboardInterrupt:
        sys.stdout.write("\nGraceful shutdown requested – exiting.\n")
        # Servers will close themselves on interpreter exit.


if __name__ == "__main__":
    main()