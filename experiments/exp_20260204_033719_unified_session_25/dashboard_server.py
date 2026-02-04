#!/usr/bin/env python3
"""
dashboard_server.py

A lightweight Flask API exposing basic swarm/experiment information.
Endpoints:
    GET /api/stats          -> Swarm health snapshot
    GET /api/tasks          -> List of all tasks with their status
    GET /api/logs?tail=N   -> Recent log lines (default tail=100)
    GET /api/experiments    -> List of known experiments
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Any

from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper utilities – these are intentionally simple placeholders.
# In a real deployment they would query the actual swarm manager,
# task scheduler, log storage, and experiment registry.
# ----------------------------------------------------------------------


def get_swarm_stats() -> Dict[str, Any]:
    """Return a dummy swarm health snapshot."""
    # Placeholder – replace with real metrics collection.
    return {
        "status": "healthy",
        "total_nodes": 12,
        "active_nodes": 11,
        "tasks_running": 34,
        "tasks_pending": 5,
    }


def get_all_tasks() -> List[Dict[str, Any]]:
    """Return a list of tasks with status information."""
    # Placeholder – replace with real task database query.
    return [
        {"id": "task-001", "experiment": "exp_alpha", "status": "running"},
        {"id": "task-002", "experiment": "exp_beta", "status": "completed"},
        {"id": "task-003", "experiment": "exp_gamma", "status": "failed"},
    ]


def tail_log_file(filepath: str, lines: int = 100) -> List[str]:
    """Read the last `lines` lines from a log file efficiently."""
    if not os.path.isfile(filepath):
        return [f"Log file not found: {filepath}"]

    # Simple implementation – for large files a more efficient approach may be required.
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()[-lines:]


def list_experiments(base_dir: str = "/app/experiments") -> List[Dict[str, Any]]:
    """Discover experiment directories and return minimal metadata."""
    experiments = []
    if not os.path.isdir(base_dir):
        return experiments

    for entry in sorted(os.listdir(base_dir)):
        exp_path = os.path.join(base_dir, entry)
        if os.path.isdir(exp_path):
            experiments.append(
                {
                    "name": entry,
                    "path": exp_path,
                    # In a real system you might read a manifest file for richer metadata.
                }
            )
    return experiments


# ----------------------------------------------------------------------
# API routes
# ----------------------------------------------------------------------


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Endpoint returning swarm health information."""
    stats = get_swarm_stats()
    return jsonify(stats)


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Endpoint returning all tasks with their current status."""
    tasks = get_all_tasks()
    return jsonify({"tasks": tasks})


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """Endpoint returning the most recent log lines.

    Query Parameters
    ----------------
    tail : int, optional
        Number of lines to return (default 100). Must be a positive integer.
    """
    tail_param = request.args.get("tail", "100")
    try:
        tail_n = max(1, int(tail_param))
    except ValueError:
        abort(400, description="Invalid 'tail' parameter; must be an integer.")

    # Adjust the path to the central application log if needed.
    log_path = os.getenv("APP_LOG_PATH", "/app/logs/app.log")
    lines = tail_log_file(log_path, tail_n)
    # Strip trailing newlines for cleaner JSON output.
    lines = [line.rstrip("\n") for line in lines]
    return jsonify({"log_path": log_path, "tail": tail_n, "lines": lines})


@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """Endpoint returning a list of known experiments."""
    exps = list_experiments()
    return jsonify({"experiments": exps})


# ----------------------------------------------------------------------
# Development entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Running directly is useful for local testing.
    # In production the Flask app would be served via a WSGI server.
    app.run(host="0.0.0.0", port=5000, debug=True)