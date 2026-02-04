#!/usr/bin/env python3
"""
Dashboard server exposing basic API endpoints for the unified session.

Endpoints:
    GET /api/stats          -> Swarm health information
    GET /api/tasks          -> List of all tasks with status
    GET /api/logs?tail=N   -> Recent log lines (default 100)
    GET /api/experiments    -> List of available experiments
"""

import os
import json
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def read_json_file(filepath):
    """Safely read a JSON file; return empty dict on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def tail_file(filepath, lines=100):
    """Return the last *lines* lines from *filepath* (as a list of strings)."""
    if not os.path.isfile(filepath):
        return []
    # Efficient tail implementation
    with open(filepath, "rb") as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        block_size = 1024
        data = b""
        while len(data.splitlines()) <= lines and f.tell() > 0:
            read_size = min(block_size, f.tell())
            f.seek(-read_size, os.SEEK_CUR)
            data = f.read(read_size) + data
            f.seek(-read_size, os.SEEK_CUR)
        lines_out = data.splitlines()[-lines:]
        return [line.decode(errors="replace") for line in lines_out]

def list_experiments(base_dir):
    """Return a list of experiment directory names under *base_dir*."""
    try:
        entries = os.listdir(base_dir)
        return [e for e in entries if os.path.isdir(os.path.join(base_dir, e))]
    except Exception:
        return []


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------
@app.route("/api/stats", methods=["GET"])
def get_stats():
    """
    Return a placeholder swarm health payload.
    In a real deployment this would aggregate node metrics, queue lengths, etc.
    """
    # Example static payload – replace with real health checks as needed.
    health = {
        "status": "healthy",
        "active_nodes": 5,
        "queued_tasks": 12,
        "cpu_usage_percent": 37.2,
        "memory_usage_percent": 68.5,
    }
    return jsonify(health)


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """
    Return a list of tasks with their current status.
    For demonstration we look for a JSON file ``tasks.json`` in the experiment root.
    """
    tasks_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    tasks = read_json_file(tasks_path)
    # Ensure a list is always returned
    if not isinstance(tasks, list):
        tasks = []
    return jsonify(tasks)


@app.route("/api/logs", methods=["GET"])
def get_logs():
    """
    Return the most recent log lines.
    Query param ``tail`` controls how many lines (default 100, max 1000).
    """
    tail_param = request.args.get("tail", default="100")
    try:
        tail_n = max(1, min(int(tail_param), 1000))
    except ValueError:
        abort(400, description="Invalid 'tail' parameter")
    # Assuming the main application log resides at /app/logs/app.log
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs", "app.log"))
    lines = tail_file(log_file, tail_n)
    return jsonify({"lines": lines})


@app.route("/api/experiments", methods=["GET"])
def get_experiments():
    """
    List all experiment directories under the top-level ``experiments`` folder.
    """
    experiments_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "experiments"))
    exp_list = list_experiments(experiments_root)
    return jsonify(exp_list)


# ----------------------------------------------------------------------
# Development entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Bind to all interfaces for container use; port can be overridden via env.
    port = int(os.getenv("DASHBOARD_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)