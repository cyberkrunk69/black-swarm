#!/usr/bin/env python3
"""
Remote Execution Client
Runs on the end‑user's machine (e.g., Dad's Mac).

Features:
1. Machine identification via MAC address.
2. Shared secret token (environment variable REMOTE_EXEC_TOKEN) for authentication.
3. TLS‑encrypted channel (optional – falls back to plain TCP if certs are absent).
4. Listens for “execute” messages from the relay server, runs the command locally,
   and sends back the result.
"""

import os
import json
import socket
import ssl
import uuid
import subprocess
import threading
from typing import Optional

# --------------------------------------------------------------------------- #
# Configuration – adjust as needed
# --------------------------------------------------------------------------- #
RELAY_HOST = os.getenv("REMOTE_RELAY_HOST", "127.0.0.1")
RELAY_PORT = int(os.getenv("REMOTE_RELAY_PORT", "12345"))
# Path to PEM files for TLS (optional). If not present, plain TCP is used.
TLS_CERTFILE = os.getenv("REMOTE_TLS_CERT", "")
TLS_KEYFILE = os.getenv("REMOTE_TLS_KEY", "")
TLS_CAFILE = os.getenv("REMOTE_TLS_CA", "")

# Shared secret token – must be the same on client & server
TOKEN = os.getenv("REMOTE_EXEC_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable REMOTE_EXEC_TOKEN must be set on the client.")

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def get_machine_id() -> str:
    """Return a stable identifier for the host (MAC address as hex string)."""
    mac_int = uuid.getnode()
    return f"{mac_int:012x}"


def create_socket() -> socket.socket:
    """Create a (optionally TLS‑wrapped) socket connected to the relay."""
    raw_sock = socket.create_connection((RELAY_HOST, RELAY_PORT))
    if TLS_CERTFILE and TLS_KEYFILE:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=TLS_CAFILE or None)
        context.load_cert_chain(certfile=TLS_CERTFILE, keyfile=TLS_KEYFILE)
        return context.wrap_socket(raw_sock, server_hostname=RELAY_HOST)
    return raw_sock


def send_json(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    # Prefix each message with its length (4‑byte big‑endian)
    sock.sendall(len(data).to_bytes(4, "big") + data)


def recv_json(sock: socket.socket) -> Optional[dict]:
    # Read length prefix
    length_bytes = sock.recv(4)
    if not length_bytes:
        return None
    length = int.from_bytes(length_bytes, "big")
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            return None
        data += chunk
    return json.loads(data.decode("utf-8"))


# --------------------------------------------------------------------------- #
# Core client logic
# --------------------------------------------------------------------------- #
def register_with_relay(sock: socket.socket) -> None:
    registration = {
        "type": "register",
        "machine_id": get_machine_id(),
        "token": TOKEN,
    }
    send_json(sock, registration)


def handle_server_messages(sock: socket.socket) -> None:
    """Continuously process messages from the relay."""
    while True:
        msg = recv_json(sock)
        if msg is None:
            print("[client] Connection closed by server.")
            break

        if msg.get("type") != "execute":
            continue  # ignore unknown messages

        # Basic auth – token must match
        if msg.get("token") != TOKEN:
            resp = {
                "type": "result",
                "machine_id": get_machine_id(),
                "command": msg.get("command"),
                "status": "error",
                "output": "Invalid authentication token.",
            }
            send_json(sock, resp)
            continue

        command = msg.get("command")
        print(f"[client] Executing command: {command}")

        try:
            completed = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output = completed.stdout
            status = "ok"
        except subprocess.CalledProcessError as e:
            output = e.stdout or e.stderr or ""
            status = "error"

        result_msg = {
            "type": "result",
            "machine_id": get_machine_id(),
            "command": command,
            "status": status,
            "output": output,
        }
        send_json(sock, result_msg)


def main() -> None:
    with create_socket() as sock:
        register_with_relay(sock)
        print("[client] Registered with relay, awaiting commands...")
        handle_server_messages(sock)


if __name__ == "__main__":
    main()