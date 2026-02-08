#!/usr/bin/env python3
"""
Remote Execution Client (WebSocket + HMAC).

This client runs on a user's machine. It connects to a relay, registers a
stable machine id, receives allow-listed commands, executes them locally, and
returns the result.

Usage:
  pip install websockets
  export REMOTE_RELAY_HOST=relay-host
  export REMOTE_RELAY_PORT=8765
  export REMOTE_RELAY_SECRET=your_shared_secret
  python remote_execution_client.py

Environment variables:
  REMOTE_RELAY_URL             Optional, overrides host/port (ws://host:port)
  REMOTE_EXEC_MACHINE_ID       Optional, override generated machine id
  REMOTE_RELAY_RECONNECT_DELAY Optional, seconds (default: 5)

Allowed commands (edit ALLOWED_COMMANDS to extend):
  - open_browser [url]
  - run <arg1> <arg2> ...  (executes without shell)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
import uuid
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

try:
    import websockets
except ImportError:  # pragma: no cover - handled in main()
    websockets = None

MACHINE_ID_FILE = Path.home() / ".remote_exec_machine_id"

DEFAULT_RELAY_HOST = os.getenv("REMOTE_RELAY_HOST", "localhost")
DEFAULT_RELAY_PORT = int(os.getenv("REMOTE_RELAY_PORT", "8765"))
DEFAULT_RELAY_SECRET = os.getenv("REMOTE_RELAY_SECRET", "change_this_secret")
DEFAULT_RELAY_URL = os.getenv("REMOTE_RELAY_URL")
DEFAULT_RECONNECT_DELAY = float(os.getenv("REMOTE_RELAY_RECONNECT_DELAY", "5"))

logger = logging.getLogger("remote_execution_client")


def _log_level(name: str) -> int:
    return getattr(logging, name.upper(), logging.INFO)


def _load_machine_id(override: str | None) -> str:
    if override:
        return override
    if MACHINE_ID_FILE.exists():
        cached = MACHINE_ID_FILE.read_text().strip()
        if cached:
            return cached
    mac = uuid.getnode()
    if (mac >> 40) % 2:
        machine_id = str(uuid.uuid4())
    else:
        machine_id = f"{mac:012x}"
    try:
        MACHINE_ID_FILE.write_text(machine_id)
    except OSError:
        pass
    return machine_id


def _sign_message(message: dict, secret: str) -> str:
    payload = json.dumps(message, sort_keys=True).encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _verify_signature(message: dict, signature: str, secret: str) -> bool:
    expected = _sign_message(message, secret)
    return hmac.compare_digest(expected, signature)


def _normalize_args(args: Iterable) -> List[str]:
    if args is None:
        return []
    if isinstance(args, list):
        return [str(item) for item in args]
    return [str(args)]


def _run_command(args: List[str]) -> Tuple[str, str]:
    if not args:
        return "", "No command arguments provided"
    proc = subprocess.run(args, capture_output=True, text=True)
    return proc.stdout or "", proc.stderr or ""


def _open_browser(args: List[str]) -> Tuple[str, str]:
    url = args[0] if args else "https://www.google.com"
    ok = webbrowser.open(url)
    if ok:
        return f"Opened {url}", ""
    return "", f"Failed to open {url}"


ALLOWED_COMMANDS: Dict[str, Callable[[List[str]], Tuple[str, str]]] = {
    "open_browser": _open_browser,
    "run": _run_command,
}


@dataclass
class ClientConfig:
    relay_url: str
    shared_secret: str
    machine_id: str
    reconnect_delay: float = 5.0


async def _handle_command(msg: dict, websocket, config: ClientConfig) -> None:
    command_id = msg.get("command_id")
    command = msg.get("command")
    args = _normalize_args(msg.get("args", []))

    response = {
        "type": "result",
        "command_id": command_id,
        "machine_id": config.machine_id,
    }

    if command not in ALLOWED_COMMANDS:
        response.update(
            {
                "output": "",
                "error": f"Command '{command}' is not allowed.",
            }
        )
    else:
        try:
            stdout, stderr = ALLOWED_COMMANDS[command](args)
            response.update({"output": stdout, "error": stderr})
        except Exception as exc:
            response.update(
                {"output": "", "error": f"Exception while executing command: {exc}"}
            )

    response["signature"] = _sign_message(response, config.shared_secret)
    await websocket.send(json.dumps(response))


async def _client_loop(config: ClientConfig) -> None:
    while True:
        try:
            async with websockets.connect(config.relay_url) as websocket:
                register_msg = {
                    "type": "register",
                    "machine_id": config.machine_id,
                }
                register_msg["signature"] = _sign_message(
                    register_msg, config.shared_secret
                )
                await websocket.send(json.dumps(register_msg))
                logger.info("Registered machine_id=%s", config.machine_id)

                async for raw_msg in websocket:
                    try:
                        msg = json.loads(raw_msg)
                    except json.JSONDecodeError:
                        logger.debug("Ignoring malformed JSON message")
                        continue

                    signature = msg.pop("signature", "")
                    if not _verify_signature(msg, signature, config.shared_secret):
                        logger.warning("Invalid signature from relay; ignoring")
                        continue

                    if msg.get("type") != "command":
                        continue
                    if msg.get("machine_id") and msg.get("machine_id") != config.machine_id:
                        continue

                    await _handle_command(msg, websocket, config)
        except Exception as exc:
            logger.warning("Relay connection error: %s", exc)
            await asyncio.sleep(config.reconnect_delay)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remote execution client")
    parser.add_argument("--relay-url", default=DEFAULT_RELAY_URL)
    parser.add_argument("--relay-host", default=DEFAULT_RELAY_HOST)
    parser.add_argument("--relay-port", type=int, default=DEFAULT_RELAY_PORT)
    parser.add_argument("--shared-secret", default=DEFAULT_RELAY_SECRET)
    parser.add_argument(
        "--machine-id",
        default=os.getenv("REMOTE_EXEC_MACHINE_ID"),
        help="Override the generated machine id",
    )
    parser.add_argument(
        "--reconnect-delay",
        type=float,
        default=DEFAULT_RECONNECT_DELAY,
        help="Seconds to wait before reconnecting",
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    return parser.parse_args()


def main() -> None:
    if websockets is None:
        sys.stderr.write("Missing dependency 'websockets'. Install with pip.\n")
        sys.exit(1)

    args = _parse_args()
    logging.basicConfig(level=_log_level(args.log_level))

    if not args.shared_secret:
        sys.stderr.write("REMOTE_RELAY_SECRET is required.\n")
        sys.exit(1)
    if args.shared_secret == "change_this_secret":
        logger.warning("Using default REMOTE_RELAY_SECRET, this is insecure.")

    relay_url = args.relay_url or f"ws://{args.relay_host}:{args.relay_port}"
    machine_id = _load_machine_id(args.machine_id)

    logger.info("Starting client for machine_id=%s", machine_id)
    logger.info("Connecting to relay at %s", relay_url)

    config = ClientConfig(
        relay_url=relay_url,
        shared_secret=args.shared_secret,
        machine_id=machine_id,
        reconnect_delay=args.reconnect_delay,
    )

    try:
        asyncio.run(_client_loop(config))
    except KeyboardInterrupt:
        logger.info("Client stopped by user")


if __name__ == "__main__":
    main()
