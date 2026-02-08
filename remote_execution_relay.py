#!/usr/bin/env python3
"""
Remote Execution Relay (WebSocket + HMAC).

The relay accepts WebSocket connections from remote_execution_client.py,
authenticates messages with an HMAC shared secret, and forwards commands to
registered clients. Results are returned to callers via the send_command()
coroutine (intended to be used by the swarm host).

Usage:
  pip install websockets
  export REMOTE_RELAY_HOST=0.0.0.0
  export REMOTE_RELAY_PORT=8765
  export REMOTE_RELAY_SECRET=your_shared_secret
  python remote_execution_relay.py
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import sys
from typing import Dict, Tuple

try:
    import websockets
except ImportError:  # pragma: no cover - handled in main()
    websockets = None

RELAY_HOST = os.getenv("REMOTE_RELAY_HOST", "0.0.0.0")
RELAY_PORT = int(os.getenv("REMOTE_RELAY_PORT", "8765"))
SHARED_SECRET = os.getenv("REMOTE_RELAY_SECRET", "change_this_secret")

logger = logging.getLogger("remote_execution_relay")

# Mapping from machine_id -> websocket connection
connected_clients: Dict[str, "websockets.WebSocketServerProtocol"] = {}
# Mapping from websocket connection -> machine_id
client_ids: Dict["websockets.WebSocketServerProtocol", str] = {}
# Mapping from command_id -> (future, machine_id)
pending_commands: Dict[str, Tuple[asyncio.Future, str]] = {}
_command_counter = 0


def _log_level(name: str) -> int:
    return getattr(logging, name.upper(), logging.INFO)


def _sign_message(message: dict) -> str:
    payload = json.dumps(message, sort_keys=True).encode()
    return hmac.new(SHARED_SECRET.encode(), payload, hashlib.sha256).hexdigest()


def _verify_signature(message: dict, signature: str) -> bool:
    expected = _sign_message(message)
    return hmac.compare_digest(expected, signature)


def _next_command_id() -> str:
    global _command_counter
    _command_counter += 1
    return f"cmd-{_command_counter}"


async def _client_handler(websocket, path=None) -> None:
    try:
        async for raw_msg in websocket:
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from client; ignoring")
                continue

            signature = msg.pop("signature", "")
            if not _verify_signature(msg, signature):
                logger.warning("Invalid signature from client; ignoring")
                continue

            msg_type = msg.get("type")
            if msg_type == "register":
                machine_id = msg.get("machine_id")
                if not machine_id:
                    logger.warning("Client registration missing machine_id")
                    continue
                connected_clients[machine_id] = websocket
                client_ids[websocket] = machine_id
                logger.info("Registered client %s", machine_id)
            elif msg_type == "result":
                cmd_id = msg.get("command_id")
                future, _ = pending_commands.pop(cmd_id, (None, None))
                if future and not future.done():
                    future.set_result(msg)
            else:
                logger.debug("Unhandled message type: %s", msg_type)
    except Exception as exc:
        logger.warning("Client connection error: %s", exc)
    finally:
        machine_id = client_ids.pop(websocket, None)
        if machine_id:
            connected_clients.pop(machine_id, None)
            for cmd_id, (future, target_id) in list(pending_commands.items()):
                if target_id == machine_id and not future.done():
                    future.set_exception(ConnectionError("Client disconnected"))
                    pending_commands.pop(cmd_id, None)
            logger.info("Client %s disconnected", machine_id)


async def send_command(
    machine_id: str, command: str, args=None, timeout: float = 30.0
) -> dict:
    """
    Send a command to a specific registered client and await its response.
    Returns a dict with keys: output, error, command_id, machine_id.
    """
    if args is None:
        args = []
    client_ws = connected_clients.get(machine_id)
    if not client_ws:
        raise ValueError(f"No connected client with machine_id {machine_id}")

    cmd_id = _next_command_id()
    command_msg = {
        "type": "command",
        "command_id": cmd_id,
        "command": command,
        "args": args,
        "machine_id": machine_id,
    }
    command_msg["signature"] = _sign_message(command_msg)

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    pending_commands[cmd_id] = (future, machine_id)

    await client_ws.send(json.dumps(command_msg))

    try:
        result = await asyncio.wait_for(future, timeout=timeout)
        return result
    except asyncio.TimeoutError as exc:
        pending_commands.pop(cmd_id, None)
        raise TimeoutError(f"Command {cmd_id} to {machine_id} timed out") from exc


async def _main() -> None:
    async with websockets.serve(_client_handler, RELAY_HOST, RELAY_PORT):
        logger.info("Relay listening on %s:%s", RELAY_HOST, RELAY_PORT)
        await asyncio.Future()  # run forever


def main() -> None:
    if websockets is None:
        sys.stderr.write("Missing dependency 'websockets'. Install with pip.\n")
        sys.exit(1)

    logging.basicConfig(level=_log_level(os.getenv("LOG_LEVEL", "INFO")))
    if SHARED_SECRET == "change_this_secret":
        logger.warning("Using default REMOTE_RELAY_SECRET, this is insecure.")

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Relay stopped by user")


if __name__ == "__main__":
    main()
