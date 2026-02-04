#!/usr/bin/env python3
"""
Dashboard server exposing basic API endpoints for the unified session.

Endpoints:
- GET /api/stats          : Swarm health information
- GET /api/tasks          : List of all tasks with their status
- GET /api/logs?tail=N    : Recent log lines (default 100)
- GET /api/experiments    : List of known experiments
"""

from flask import Flask, jsonify, request, abort
import os
import json
from pathlib import Path
from typing import List

app = Flask(__name__)

# ----------------------------------------------------------------------
# Helper functions – in a real system these would query the actual
# orchestrator, database, or log storage.  Here we provide simple
# deterministic placeholders so the API works out‑of‑the‑box.
# ----------------------------------------------------------------------


def get_swarm_health() -> dict:
    """Return a mock health status for the compute swarm."""
    # Example fields – adjust as needed for the real implementation.
    return {
        "total_nodes": 12,
        "active_nodes": 11,
        "idle_nodes": 1,
        "cpu_usage_percent": 57.3,
        "memory_usage_percent": 68.1,
        "last_updated": "2026-02-04T12:00:00Z"
    }


def get_all_tasks() -> List[dict]:
    """Return a mock list of tasks with status."""
    # In a production system this would read from a task manager or DB.
    return [
        {"id": "task-001", "name": "data_ingest", "status": "completed"},
        {"id": "task-002", "name": "model_train", "status": "running"},
        {"id": "task-003", "name": "evaluation", "status": "queued"},
        {"id": "task-004", "name": "report_gen", "status": "failed"},
    ]


def get_recent_logs(tail: int = 100) -> List[str]:
    """
    Return the last `tail` lines from the combined log file.
    If a log file does not exist, an empty list is returned.
    """
    # Look for a generic log file in the workspace root.
    log_path = Path("/app") / "dashboard.log"
    if not log_path.is_file():
        return []

    # Read from the end efficiently.
    with open(log_path, "r", encoding="utf-8") as f:
        # Simple approach: read all and slice – acceptable for modest log sizes.
        lines = f.readlines()
        return [line.rstrip("\n") for line in lines[-tail:]]


def get_experiment_list() -> List[dict]:
    """
    Scan the /app/experiments directory for sub‑folders that look like
    experiment runs and return a summary.
    """
    experiments_root = Path("/app") / "experiments"
    if not experiments_root.is_dir():
        return []

    exp_list = []
    for entry in experiments_root.iterdir():
        if entry.is_dir():
            # Try to read a metadata.json if present.
            meta_path = entry / "metadata.json"
            meta = {}
            if meta_path.is_file():
                try:
                    meta = json.load(open(meta_path, "r", encoding="utf-8"))
                except Exception:
                    pass
            exp_list.append({
                "id": entry.name,
                "path": str(entry),
                "description": meta.get("description", ""),
                "created_at": meta.get("created_at", ""),
            })
    return exp_list


# ----------------------------------------------------------------------
# API route definitions
# ----------------------------------------------------------------------


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """Return swarm health JSON."""
    return jsonify(get_swarm_health())


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    """Return all tasks with their current status."""
    return jsonify(get_all_tasks())


@app.route("/api/logs", methods=["GET"])
def api_logs():
    """Return recent log lines; `tail` query param controls line count."""
    tail_param = request.args.get("tail", default="100")
    try:
        tail = int(tail_param)
        if tail < 0:
            raise ValueError()
    except ValueError:
        abort(400, description="Invalid `tail` parameter; must be a non‑negative integer.")
    logs = get_recent_logs(tail)
    return jsonify({"lines": logs, "tail": tail})


@app.route("/api/experiments", methods=["GET"])
def api_experiments():
    """Return a list of discovered experiments."""
    return jsonify(get_experiment_list())


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # The host/port can be overridden via environment variables if needed.
    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "5000"))
    app.run(host=host, port=port, debug=False)