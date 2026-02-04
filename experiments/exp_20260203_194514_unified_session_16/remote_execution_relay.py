import socket
import ssl
import json
import subprocess
import threading
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class RemoteExecutionRelay:
    """
    Server‑side component that:
    1. Accepts TLS‑encrypted connections from RemoteExecutionClient instances.
    2. Authenticates each request using a pre‑shared token per machine_id.
    3. Validates that the requested command is within an allowed whitelist.
    4. Executes the command locally (i.e., on the host where this relay runs – which
       should be the user's own machine when the client runs on that same LAN node).
    5. Sends a JSON response containing stdout, stderr and an execution status.
    """

    # Example static whitelist – in production this would be configurable.
    COMMAND_WHITELIST = {
        "open": ["open"],                     # macOS open command
        "start": ["start"],                   # Windows start command
        "xdg-open": ["xdg-open"],             # Linux desktop opener
        "echo": ["echo"],                     # harmless demo
    }

    # Mapping of machine_id -> token (would normally be loaded from a secure store)
    AUTH_TOKENS: Dict[str, str] = {
        # "machine_id": "shared_secret"
        # Example entry – replace with real values.
        # "00:11:22:33:44:55": "s3cr3tTokenForMac01",
    }

    def __init__(self, bind_host: str = "0.0.0.0", bind_port: int = 8443,
                 certfile: str = "certs/relay_cert.pem",
                 keyfile: str = "certs/relay_key.pem"):
        self.bind_addr = (bind_host, bind_port)
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(self.bind_addr)
        self.sock.listen(5)
        logging.info(f"RemoteExecutionRelay listening on {bind_host}:{bind_port}")

    def serve_forever(self):
        while True:
            client_sock, client_addr = self.sock.accept()
            tls_sock = self.context.wrap_socket(client_sock, server_side=True)
            threading.Thread(target=self._handle_client,
                             args=(tls_sock, client_addr),
                             daemon=True).start()

    def _handle_client(self, conn: ssl.SSLSocket, addr):
        logging.info(f"Connection from {addr}")
        try:
            # Simple length‑prefixed framing
            length_bytes = self._recvall(conn, 4)
            if not length_bytes:
                raise ConnectionError("Failed to read length prefix")
            msg_len = int.from_bytes(length_bytes, "big")
            payload = self._recvall(conn, msg_len)
            if not payload:
                raise ConnectionError("Failed to read full payload")
            request = json.loads(payload.decode("utf-8"))
            response = self._process_request(request)
        except Exception as exc:
            logging.exception("Error handling request")
            response = {"status": "error", "error": str(exc)}
        finally:
            resp_bytes = json.dumps(response).encode("utf-8")
            conn.sendall(len(resp_bytes).to_bytes(4, "big") + resp_bytes)
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            logging.info(f"Closed connection from {addr}")

    def _process_request(self, req: dict) -> dict:
        # 1️⃣ Authentication
        machine_id = req.get("machine_id")
        token = req.get("token")
        if not machine_id or not token:
            return {"status": "unauthenticated", "error": "Missing machine_id or token"}

        expected_token = self.AUTH_TOKENS.get(machine_id)
        if expected_token is None:
            return {"status": "unauthenticated", "error": "Unknown machine_id"}
        if token != expected_token:
            return {"status": "unauthenticated", "error": "Invalid token"}

        # 2️⃣ Command validation
        raw_cmd = req.get("command", "")
        if not raw_cmd:
            return {"status": "invalid", "error": "Empty command"}

        # Split for whitelist checking (simple space split – more robust parsing can be added)
        parts = raw_cmd.strip().split()
        base_cmd = parts[0]

        allowed = any(base_cmd == allowed_cmd for allowed_cmd in self._flatten_whitelist())
        if not allowed:
            return {"status": "forbidden", "error": f"Command '{base_cmd}' not permitted"}

        # 3️⃣ Execution
        try:
            completed = subprocess.run(
                raw_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # safety timeout
            )
            return {
                "status": "ok",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timed out"}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    @staticmethod
    def _flatten_whitelist():
        """Utility to get a flat list of allowed base commands."""
        flat = []
        for cmds in RemoteExecutionRelay.COMMAND_WHITELIST.values():
            flat.extend(cmds)
        return flat

    @staticmethod
    def _recvall(conn: ssl.SSLSocket, n: int) -> bytes:
        """Receive exactly n bytes or return None."""
        data = b""
        while len(data) < n:
            chunk = conn.recv(n - len(data))
            if not chunk:
                return None
            data += chunk
        return data


if __name__ == "__main__":
    # In a real deployment, cert/key files would be generated beforehand.
    # For quick testing you can generate a self‑signed cert with:
    #   openssl req -newkey rsa:2048 -nodes -keyout relay_key.pem -x509 -days 365 -out relay_cert.pem
    relay = RemoteExecutionRelay(
        bind_host="0.0.0.0",
        bind_port=8443,
        certfile="certs/relay_cert.pem",
        keyfile="certs/relay_key.pem"
    )
    try:
        relay.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down RemoteExecutionRelay")