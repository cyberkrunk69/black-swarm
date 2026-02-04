#!/usr/bin/env python3
"""
dashboard_server.py

Simple Flask based HTTP API exposing basic information about the
current workspace / experiment.  The endpoints are:

* GET /api/stats          – Swarm health / general statistics
* GET /api/tasks          – List of all tasks with their status
* GET /api/logs?tail=N    – Recent log lines (default 100)
* GET /api/experiments    – List of known experiments

All responses are JSON.  The implementation uses in‑memory placeholder
data; in a real deployment these helpers would query the actual
runtime / storage back‑ends.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import List, Dict, Any

from flask import Flask, request, jsonify

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper stubs – replace with real logic as needed
# ----------------------------------------------------------------------


def get_swarm_stats() -> Dict[str, Any]:
    """
    Return a dictionary describing the health of the swarm.
    Placeholder values are provided for demonstration.
    """
    return {
        "nodes_total": 5,
        "nodes_active": 4,
        "tasks_running": 12,
        "tasks_pending": 3,
        "uptime_seconds": 86400,
    }


def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Return a list of task descriptors.  Each descriptor contains at least
    an identifier and a status string.
    """
    # Dummy data – in practice this would be loaded from a DB / scheduler
    return [
        {"id": "task-001", "status": "running"},
        {"id": "task-002", "status": "completed"},
        {"id": "task-003", "status": "failed"},
        {"id": "task-004", "status": "pending"},
    ]


def read_recent_logs(tail: int = 100) -> List[str]:
    """
    Return the last ``tail`` lines from the central log file.
    If the log file does not exist, an empty list is returned.
    """
    # Assume a conventional log location relative to the workspace root.
    log_path = pathlib.Path(__file__).resolve().parents[2] / "logs" / "dashboard.log"
    if not log_path.is_file():
        return []

    # Efficient tail implementation – read from the end of the file.
    # For simplicity and given the modest default size, we read all lines.
    with log_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    return [line.rstrip("\n") for line in lines[-tail:]]


def list_experiments() -> List[Dict[str, Any]]:
    """
    Scan the ``experiments`` directory for sub‑folders that look like
    experiments and return a minimal description.
    """
    experiments_root = pathlib.Path(__file__).resolve().parents[2] / "experiments"
    exp_list: List[Dict[str, Any]] = []
    if experiments_root.is_dir():
        for entry in experiments_root.iterdir():
            if entry.is_dir() and entry.name.startswith("exp_"):
                exp_list.append(
                    {
                        "id": entry.name,
                        "path": str(entry.relative_to(experiments_root.parent)),
                    }
                )
    return exp_list


# ----------------------------------------------------------------------
# API Endpoints
# ----------------------------------------------------------------------


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return swarm health statistics."""
    stats = get_swarm_stats()
    return jsonify(stats)


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Return a list of all tasks with their current status."""
    tasks = get_all_tasks()
    return jsonify(tasks)


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """
    Return the most recent log lines.
    Query param ``tail`` controls how many lines are returned (default 100).
    """
    tail_str = request.args.get("tail", "100")
    try:
        tail = max(0, int(tail_str))
    except ValueError:
        return jsonify({"error": "Invalid tail parameter"}), 400

    logs = read_recent_logs(tail)
    return jsonify(logs)


@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """Return a list of discovered experiments."""
    experiments = list_experiments()
    return jsonify(experiments)


# ----------------------------------------------------------------------
# Entrypoint
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> int:
    """
    Run the Flask development server.  In production you would likely
    deploy this via a WSGI container (gunicorn, uwsgi, etc.).
    """
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "5000"))
    app.run(host=host, port=port, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())