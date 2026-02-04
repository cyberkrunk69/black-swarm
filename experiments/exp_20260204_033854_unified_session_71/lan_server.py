import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from typing import Tuple, Optional


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_client_ip(handler: BaseHTTPRequestHandler) -> str:
    """
    Extract the client IP address from the handler.
    """
    return handler.client_address[0]


def is_localhost(ip: str) -> bool:
    """
    Returns True if the given IP address is a loopback address.
    """
    return ip == "127.0.0.1" or ip == "::1"


# ----------------------------------------------------------------------
# Base Server implementation
# ----------------------------------------------------------------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    A simple threaded HTTP server.
    """
    daemon_threads = True


class BaseServer:
    """
    Common functionality for both AdminServer and LANServer.
    """
    def __init__(self, host: str, port: int, required_privilege: str):
        self.host = host
        self.port = port
        self.required_privilege = required_privilege
        self._httpd: Optional[ThreadedHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def _make_handler(self):
        parent = self

        class RequestHandler(BaseHTTPRequestHandler):
            def _enforce_privilege(self) -> bool:
                """
                Checks the X-Privilege header against the required privilege.
                """
                privilege = self.headers.get("X-Privilege", "")
                return privilege == parent.required_privilege

            def _reject(self, code: int, message: str):
                self.send_response(code)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(message.encode())

            def do_GET(self):
                client_ip = get_client_ip(self)

                # Privilege enforcement
                if not self._enforce_privilege():
                    self._reject(403, "Forbidden: insufficient privilege")
                    return

                # Simple routing logic – subclasses can extend this
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "server": parent.__class__.__name__,
                    "client_ip": client_ip,
                    "message": "Hello from %s!" % parent.__class__.__name__
                }
                import json
                self.wfile.write(json.dumps(response).encode())

            def log_message(self, format: str, *args):
                # Override to suppress default console logging; replace with
                # a minimal log if desired.
                return

        return RequestHandler

    def start(self):
        """
        Starts the HTTP server in a background thread.
        """
        handler_cls = self._make_handler()
        self._httpd = ThreadedHTTPServer((self.host, self.port), handler_cls)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            name=f"{self.__class__.__name__}-Thread",
            daemon=True,
        )
        self._thread.start()
        print(f"[{self.__class__.__name__}] Listening on {self.host}:{self.port}")

    def stop(self):
        """
        Gracefully stops the server.
        """
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread:
            self._thread.join()
            self._thread = None
        print(f"[{self.__class__.__name__}] Stopped.")


# ----------------------------------------------------------------------
# Specific server implementations
# ----------------------------------------------------------------------
class AdminServer(BaseServer):
    """
    Admin server – binds only to localhost (127.0.0.1) and requires
    the 'admin' privilege.
    """
    def __init__(self, port: int = 8000):
        super().__init__(host="127.0.0.1", port=port, required_privilege="admin")


class LANServer(BaseServer):
    """
    LAN server – binds to all interfaces (0.0.0.0) but restricts access
    to non‑loopback addresses. Requires the 'user' privilege.
    """
    def __init__(self, port: int = 8001):
        super().__init__(host="0.0.0.0", port=port, required_privilege="user")

    def _make_handler(self):
        """
        Overrides the base handler to add LAN‑specific IP checks.
        """
        parent = self

        class LANRequestHandler(BaseServer._make_handler(self)):
            def do_GET(self):
                client_ip = get_client_ip(self)

                # Reject loopback requests – they should go to AdminServer
                if is_localhost(client_ip):
                    self._reject(403, "Forbidden: loopback access not allowed on LAN server")
                    return

                # Continue with normal processing (privilege check, etc.)
                super().do_GET()

        return LANRequestHandler


# ----------------------------------------------------------------------
# Convenience entry point for manual testing
# ----------------------------------------------------------------------
if __name__ == "__main__":
    admin_srv = AdminServer()
    lan_srv = LANServer()

    admin_srv.start()
    lan_srv.start()

    try:
        # Keep the main thread alive while servers run in background threads.
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        admin_srv.stop()
        lan_srv.stop()