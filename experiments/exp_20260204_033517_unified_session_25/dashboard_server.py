#!/usr/bin/env python3
"""
Dashboard server exposing basic API endpoints for the platform.

Endpoints:
- GET /api/stats               : Swarm health information.
- GET /api/tasks               : List of all tasks with their status.
- GET /api/logs?tail=N         : Recent log lines (default 100).
- GET /api/experiments         : List of available experiments.

The implementation uses Flask and provides placeholder data where
real back‑ends are not defined. Adjust the data‑retrieval helpers to
integrate with your actual system.
"""

import os
import json
from flask import Flask, jsonify, request, abort
from pathlib import Path

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def get_swarm_health():
    """
    Placeholder for actual swarm health logic.
    Returns a dict that can be extended with real metrics.
    """
    # In a real system you might query Docker Swarm, Kubernetes, etc.
    return {"status": "healthy", "nodes_active": 5, "tasks_running": 12}


def list_tasks():
    """
    Placeholder for task enumeration.
    Returns a list of dicts each describing a task.
    """
    # Replace with real task manager integration.
    sample_tasks = [
        {"id": "task-1", "name": "data_ingest", "status": "completed"},
        {"id": "task-2", "name": "model_train", "status": "running"},
        {"id": "task-3", "name": "evaluation", "status": "queued"},
    ]
    return sample_tasks


def read_recent_logs(tail: int = 100):
    """
    Reads the last `tail` lines from the main application log.
    If the log file does not exist, returns an empty list.
    """
    log_path = Path("/app/logs/app.log")
    if not log_path.is_file():
        return []

    # Efficient tail implementation
    with log_path.open("rb") as f:
        # Seek from end and read backwards until we have enough lines
        f.seek(0, os.SEEK_END)
        buffer = bytearray()
        lines_found = 0
        pointer_location = f.tell()

        while pointer_location > 0 and lines_found <= tail:
            # Read in chunks
            chunk_size = min(1024, pointer_location)
            f.seek(pointer_location - chunk_size)
            chunk = f.read(chunk_size)
            buffer = chunk + buffer
            lines_found = buffer.count(b'\n')
            pointer_location -= chunk_size

        # Decode and split, keep only the last `tail` lines
        all_lines = buffer.decode(errors="replace").splitlines()
        return all_lines[-tail:]


def list_experiments():
    """
    Scans the `/app/experiments` directory and returns a list of experiment
    identifiers (folder names).
    """
    experiments_root = Path("/app/experiments")
    if not experiments_root.is_dir():
        return []

    return sorted([p.name for p in experiments_root.iterdir() if p.is_dir()])


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return swarm health statistics."""
    health = get_swarm_health()
    return jsonify(health)


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Return a list of all tasks with their current status."""
    tasks = list_tasks()
    return jsonify(tasks)


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """
    Return recent log lines.
    Query param:
        tail (int) – number of lines to return (default 100, max 1000)
    """
    try:
        tail_param = request.args.get("tail", default="100")
        tail = int(tail_param)
        tail = max(1, min(tail, 1000))  # clamp to reasonable bounds
    except ValueError:
        abort(400, description="Invalid 'tail' parameter; must be an integer.")

    lines = read_recent_logs(tail)
    return jsonify({"lines": lines, "tail": tail})


@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """Return a list of available experiments."""
    experiments = list_experiments()
    return jsonify(experiments)


# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # For development only; in production use a WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=False)