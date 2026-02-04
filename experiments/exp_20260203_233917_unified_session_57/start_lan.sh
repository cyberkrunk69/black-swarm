#!/usr/bin/env bash
# Startup script for the LANServer (listens on all interfaces)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"
exec python "${SCRIPT_DIR}/lan_server.py" --lan