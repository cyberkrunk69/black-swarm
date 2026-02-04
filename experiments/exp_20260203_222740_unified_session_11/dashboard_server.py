#!/usr/bin/env python3
"""
Dashboard server exposing simple JSON APIs for the Claude Parasite Brain Suck project.

Endpoints:
    GET /api/stats               – Swarm health summary
    GET /api/tasks               – List of tasks with their current status
    GET /api/logs?tail=N         – Tail of the main application log (default 100 lines)
    GET /api/experiments         – List of available experiment directories
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


def read_log_tail(log_path: Path, lines: int = 100) -> List[str]:
    """Return the last `lines` lines from `log_path`."""
    if not log_path.is_file():
        return [f"Log file not found: {log_path}"]
    # Efficient tail implementation
    with log_path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        buffer = bytearray()
        block_size = 1024
        while len(buffer) < lines * 100 and f.tell() > 0:
            seek = max(0, f.tell() - block_size)
            f.seek(seek)
            buffer = f.read(min(block_size, f.tell())) + buffer
            f.seek(seek)
        lines_bytes = buffer.splitlines()[-lines:]
        return [line.decode(errors="replace") for line in lines_bytes]


def get_experiment_list(base_dir: Path) -> List[Dict[str, Any]]:
    """Return a list of experiments (directories) under `base_dir`."""
    experiments = []
    for entry in sorted(base_dir.iterdir()):
        if entry.is_dir() and entry.name.startswith("exp_"):
            experiments.append({
                "name": entry.name,
                "path": str(entry.relative_to(base_dir.parent)),
            })
    return experiments


def mock_swarm_health() -> Dict[str, Any]:
    """Placeholder for real swarm health data."""
    return {
        "active_nodes": 5,
        "idle_nodes": 2,
        "failed_nodes": 0,
        "queue_length": 12,
        "last_updated": "2026-02-04T12:00:00Z"
    }


def mock_tasks() -> List[Dict[str, Any]]:
    """Placeholder for real task data."""
    return [
        {"id": "task-001", "status": "running", "started_at": "2026-02-04T11:45:00Z"},
        {"id": "task-002", "status": "queued", "queued_at": "2026-02-04T11:50:00Z"},
        {"id": "task-003", "status": "completed", "finished_at": "2026-02-04T11:30:00Z"},
    ]


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return swarm health information."""
    return jsonify(mock_swarm_health())


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Return the list of tasks with their status."""
    return jsonify(mock_tasks())


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """Return the last N lines of the application log."""
    tail_param = request.args.get("tail", default="100")
    try:
        tail = int(tail_param)
        if tail <= 0:
            raise ValueError()
    except ValueError:
        abort(400, description="Invalid 'tail' parameter; must be a positive integer")

    # Assume a top‑level logs directory; adjust as needed.
    log_file = Path(__file__).parents[2] / "logs" / "app.log"
    lines = read_log_tail(log_file, tail)
    return jsonify({"log_path": str(log_file), "tail": tail, "lines": lines})


@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """Return a list of experiment directories."""
    base_dir = Path(__file__).parents[1]  # experiments/<exp_id>
    experiments = get_experiment_list(base_dir.parent)
    return jsonify(experiments)


# ----------------------------------------------------------------------
# Development entry point
# ----------------------------------------------------------------------


if __name__ == "__main__":
    # For quick local testing; in production run via a WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=True)