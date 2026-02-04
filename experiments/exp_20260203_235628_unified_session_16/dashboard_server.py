```python
"""
dashboard_server.py

A lightweight FastAPI server exposing basic monitoring endpoints for the
Claude‑Parasite‑Brain‑Suck project.

Endpoints:
    GET /api/stats          – overall swarm health statistics
    GET /api/tasks          – list of all tasks with their current status
    GET /api/logs?tail=N    – recent log lines (default 100)
    GET /api/experiments    – list of known experiments
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Claude Parasite Brain Suck – Dashboard API")

# --------------------------------------------------------------------------- #
# Helper utilities – in a real system these would query the actual runtime
# --------------------------------------------------------------------------- #

BASE_DIR = Path(__file__).resolve().parent.parent  # workspace root (..)
LOG_FILE = BASE_DIR / "logs" / "system.log"        # example log location
EXPERIMENTS_DIR = BASE_DIR / "experiments"


def load_json_file(filepath: Path) -> Any:
    """Safely load a JSON file; return {} on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_swarm_stats() -> Dict[str, Any]:
    """
    Return a dictionary representing swarm health.
    In production this would aggregate metrics from workers, queues, etc.
    """
    # Placeholder static data – replace with real metrics as needed
    return {
        "active_workers": 12,
        "queued_tasks": 34,
        "completed_tasks": 578,
        "failed_tasks": 7,
        "cpu_usage_percent": 42.3,
        "memory_usage_percent": 68.9,
    }


def get_all_tasks() -> List[Dict[str, Any]]:
    """
    Retrieve a list of all tasks with status.
    This demo loads a JSON file `tasks.json` if present.
    """
    tasks_path = BASE_DIR / "data" / "tasks.json"
    data = load_json_file(tasks_path)
    # Expected format: [{"id": "...", "status": "...", ...}, ...]
    if isinstance(data, list):
        return data
    return []


def get_recent_logs(tail: int = 100) -> List[str]:
    """
    Return the last `tail` lines from the system log.
    If the log file does not exist, return an empty list.
    """
    if not LOG_FILE.is_file():
        return []

    try:
        # Efficient tail implementation for moderate sizes
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Read all lines then slice; for huge logs you would stream backwards.
            lines = f.readlines()
            return [line.rstrip("\n") for line in lines[-tail:]]
    except Exception:
        return []


def list_experiments() -> List[Dict[str, Any]]:
    """
    Scan the experiments directory and return a list of experiment metadata.
    Each experiment folder may contain a `metadata.json` file.
    """
    experiments = []
    if not EXPERIMENTS_DIR.is_dir():
        return experiments

    for exp_dir in EXPERIMENTS_DIR.iterdir():
        if not exp_dir.is_dir():
            continue
        meta_path = exp_dir / "metadata.json"
        meta = load_json_file(meta_path) if meta_path.is_file() else {}
        experiments.append({
            "name": exp_dir.name,
            "path": str(exp_dir),
            "metadata": meta,
        })
    return experiments


# --------------------------------------------------------------------------- #
# API endpoints
# --------------------------------------------------------------------------- #

@app.get("/api/stats", response_class=JSONResponse)
def api_stats():
    """Return swarm health statistics."""
    stats = get_swarm_stats()
    return JSONResponse(content=stats)


@app.get("/api/tasks", response_class=JSONResponse)
def api_tasks():
    """Return a list of all tasks with their current status."""
    tasks = get_all_tasks()
    return JSONResponse(content={"tasks": tasks, "count": len(tasks)})


@app.get("/api/logs", response_class=JSONResponse)
def api_logs(tail: Optional[int] = Query(100, ge=1, le=10000)):
    """
    Return the most recent log lines.
    Query parameter:
        tail (int): number of lines to return (default 100, max 10 000)
    """
    logs = get_recent_logs(tail)
    return JSONResponse(content={"tail": tail, "lines": logs})


@app.get("/api/experiments", response_class=JSONResponse)
def api_experiments():
    """Return a list of known experiments."""
    exps = list_experiments()
    return JSONResponse(content={"experiments": exps, "count": len(exps)})

# --------------------------------------------------------------------------- #
# Development convenience – run with `uvicorn dashboard_server:app`
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("dashboard_server:app", host="0.0.0.0", port=8000, reload=True)
```