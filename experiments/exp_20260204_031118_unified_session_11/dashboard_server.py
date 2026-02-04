#!/usr/bin/env python3
"""
dashboard_server.py

Simple Flask based HTTP API exposing basic swarm/experiment information.
All endpoints return JSON payloads.

Endpoints:
    GET /api/stats
        - Swarm health summary (mock data).

    GET /api/tasks
        - List of all known tasks with their status (mock data).

    GET /api/logs?tail=N
        - Returns the last N lines from the server log file (defaults to 100).

    GET /api/experiments
        - Enumerates experiment directories under the workspace ``experiments/``.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def read_last_lines(file_path: Path, n: int) -> List[str]:
    """Return the last *n* lines from *file_path*."""
    if not file_path.is_file():
        return [f"Log file not found: {file_path}"]
    # Efficient tail implementation
    with file_path.open("rb") as f:
        # Seek from end in chunks until we have enough newlines
        f.seek(0, os.SEEK_END)
        buffer = bytearray()
        pointer = f.tell()
        while pointer > 0 and len(buffer.splitlines()) <= n:
            block_size = min(4096, pointer)
            pointer -= block_size
            f.seek(pointer)
            buffer = f.read(block_size) + buffer
        lines = buffer.splitlines()[-n:]
        # Decode each line safely
        return [line.decode(errors="replace") for line in lines]

def get_experiment_list(base_dir: Path) -> List[Dict[str, Any]]:
    """Return a list of experiments found under *base_dir*."""
    experiments = []
    if not base_dir.is_dir():
        return experiments
    for entry in sorted(base_dir.iterdir()):
        if entry.is_dir() and entry.name.startswith("exp_"):
            experiments.append({
                "id": entry.name,
                "path": str(entry.relative_to(base_dir.parent)),
                # Placeholder metadata – could be extended later
                "created": entry.stat().st_ctime,
            })
    return experiments

# ----------------------------------------------------------------------
# Mock data generators (replace with real integrations as needed)
# ----------------------------------------------------------------------
def mock_swarm_stats() -> Dict[str, Any]:
    """Generate dummy swarm health statistics."""
    return {
        "total_nodes": 12,
        "active_nodes": 11,
        "idle_nodes": 1,
        "tasks_running": 7,
        "tasks_pending": 3,
        "tasks_failed": 0,
        "uptime_seconds": 86400,
    }

def mock_task_list() -> List[Dict[str, Any]]:
    """Generate a dummy list of tasks with status."""
    return [
        {"task_id": f"task_{i}", "status": "running" if i % 3 else "completed",
         "started_at": "2026-02-04T12:00:00Z",
         "node": f"node-{i%5}"}
        for i in range(1, 11)
    ]

# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return swarm health information."""
    return jsonify(mock_swarm_stats())

@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Return the list of tasks with their current status."""
    return jsonify(mock_task_list())

@app.route("/api/logs", methods=["GET"])
def api_logs():
    """
    Return the last N lines of the server log.
    Query param:
        tail (int) – number of lines to return (default 100)
    """
    tail_param = request.args.get("tail", default="100")
    try:
        tail = int(tail_param)
        if tail < 0:
            raise ValueError()
    except ValueError:
        abort(400, description="Invalid 'tail' parameter; must be a non‑negative integer.")

    # Assume a log file named `dashboard_server.log` in the same directory
    log_path = Path(__file__).with_name("dashboard_server.log")
    lines = read_last_lines(log_path, tail)
    return jsonify({"log_path": str(log_path), "lines": lines, "tail": tail})

@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """
    Enumerate experiments present under the workspace's ``experiments/`` folder.
    """
    workspace_root = Path(__file__).parents[2]  # /app
    experiments_dir = workspace_root / "experiments"
    exp_list = get_experiment_list(experiments_dir)
    return jsonify(exp_list)

# ----------------------------------------------------------------------
# Entry point for running directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Bind to all interfaces; adjust host/port as needed.
    app.run(host="0.0.0.0", port=5000, debug=False)