#!/usr/bin/env python3
"""
Remote Execution Relay (Server side)

Responsibilities:
1. Accept client registrations (machine_id + token).
2. Accept command requests from any authorized source.
3. Validate token and command‑scope whitelist.
4. Forward commands to the appropriate client.
5. Route the client’s result back to the original requester.
"""

import os
import json
import socket
import ssl
import threading
from typing import Dict, Tuple, Optional

# --------------------------------------------------------------------------- #
# Configuration – adjust as needed
# --------------------------------------------------------------------------- #
LISTEN_HOST = os.getenv("RELAY_LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.getenv("RELAY_LISTEN_PORT", "12345"))

# TLS configuration (optional). If cert/key are provided, the server uses TLS.
TLS_CERTFILE = os.getenv("RELAY_TLS_CERT", "")
TLS_KEYFILE = os.getenv("RELAY_TLS_KEY", "")
TLS_CAFILE = os.getenv("RELAY_TLS_CA", "")

# Shared secret token – must match the client’s environment variable.
TOKEN = os.getenv("REMOTE_EXEC_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable REMOTE_EXEC_TOKEN must be set on the server.")

# --------------------------------------------------------------------------- #
# Simple command‑scope whitelist (per machine). Extend as needed.
# Example: {"machine_id": ["open my browser", "ls", "pwd"]}
# An empty list means “allow any command”.
# --------------------------------------------------------------------------- #
COMMAND_WHITELIST: Dict[str, list] = {
    # "0123456789ab": ["open my browser", "ls", "pwd"],
}

# --------------------------------------------------------------------------- #
# Helper utilities for length‑prefixed JSON messages
# --------------------------------------------------------------------------- #
def send_json(sock: socket.socket, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    sock.sendall(len(data).to_bytes(4, "big") + data)


def recv_json(sock: socket.socket) -> Optional[dict]:
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
# Core server state
# --------------------------------------------------------------------------- #
# Mapping: machine_id -> (socket, address)
registered_clients: Dict[str, Tuple[socket.socket, Tuple[str, int]]] = {}
# Lock to protect the above dict
clients_lock = threading.Lock()


def client_handler(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """
    Handles a single connection which can be either:
    * a client registration (type == "register")
    * a command request (type == "command")
    """
    try:
        while True:
            msg = recv_json(conn)
            if msg is None:
                break  # connection closed

            msg_type = msg.get("type")
            if msg_type == "register":
                handle_registration(conn, addr, msg)
                # After registration we keep the socket open to receive execute/result msgs.
                # The loop continues to listen for result messages from that client.
            elif msg_type == "command":
                handle_command_request(conn, msg)
                # For a command request we *do not* keep the socket; we just forward
                # the command to the target client and later send the result back.
                # The client that sent the command stays connected for the duration
                # of the request (single‑use socket pattern).
                break
            elif msg_type == "result":
                # Result messages come from registered clients.
                forward_result_to_requester(msg)
            else:
                # Unknown message – ignore
                continue
    finally:
        # Cleanup on disconnect – remove any registration that used this socket
        with clients_lock:
            to_remove = [mid for mid, (s, _) in registered_clients.items() if s == conn]
            for mid in to_remove:
                del registered_clients[mid]
        conn.close()


def handle_registration(conn: socket.socket, addr: Tuple[str, int], msg: dict) -> None:
    token = msg.get("token")
    machine_id = msg.get("machine_id")
    if token != TOKEN or not machine_id:
        send_json(conn, {"type": "error", "reason": "authentication_failed"})
        return

    with clients_lock:
        registered_clients[machine_id] = (conn, addr)
    send_json(conn, {"type": "registered", "machine_id": machine_id})
    print(f"[relay] Registered client {machine_id} from {addr}")


def is_command_allowed(machine_id: str, command: str) -> bool:
    whitelist = COMMAND_WHITELIST.get(machine_id, [])
    if not whitelist:  # empty list => allow any command
        return True
    return command in whitelist


def handle_command_request(requester_sock: socket.socket, msg: dict) -> None:
    token = msg.get("token")
    target_id = msg.get("machine_id")
    command = msg.get("command")

    if token != TOKEN:
        send_json(requester_sock, {"type": "error", "reason": "authentication_failed"})
        return

    if not target_id or not command:
        send_json(requester_sock, {"type": "error", "reason": "invalid_payload"})
        return

    if not is_command_allowed(target_id, command):
        send_json(requester_sock, {"type": "error", "reason": "command_not_allowed"})
        return

    with clients_lock:
        client_entry = registered_clients.get(target_id)

    if not client_entry:
        send_json(requester_sock, {"type": "error", "reason": "client_not_connected"})
        return

    client_sock, _ = client_entry

    # Build the execute message and send it to the client.
    exec_msg = {
        "type": "execute",
        "command": command,
        "token": TOKEN,  # client will verify this
    }
    send_json(client_sock, exec_msg)

    # Wait for the result from the client (blocking read on the client socket).
    # The client will send a "result" message back on the same socket.
    result = recv_json(client_sock)
    if result and result.get("type") == "result":
        # Forward the result back to the original requester.
        send_json(requester_sock, result)
    else:
        send_json(requester_sock, {"type": "error", "reason": "no_result_received"})


def forward_result_to_requester(result_msg: dict) -> None:
    """
    In this simplified implementation we only support the request‑response pattern
    handled directly in `handle_command_request`. Therefore this function is a
    placeholder for more complex routing (e.g., when multiple requesters share a
    persistent connection). It can be expanded later.
    """
    pass  # No‑op for now


def start_server() -> None:
    raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    raw_sock.bind((LISTEN_HOST, LISTEN_PORT))
    raw_sock.listen(10)
    print(f"[relay] Listening on {LISTEN_HOST}:{LISTEN_PORT}")

    if TLS_CERTFILE and TLS_KEYFILE:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=TLS_CERTFILE, keyfile=TLS_KEYFILE)
        if TLS_CAFILE:
            context.load_verify_locations(cafile=TLS_CAFILE)
        server_sock = context.wrap_socket(raw_sock, server_side=True)
    else:
        server_sock = raw_sock

    try:
        while True:
            conn, addr = server_sock.accept()
            threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()
    finally:
        server_sock.close()


if __name__ == "__main__":
    start_server()