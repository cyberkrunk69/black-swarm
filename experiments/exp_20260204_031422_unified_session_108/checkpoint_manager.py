"""Checkpoint manager for unified session experiments.

This module provides utilities to persist and restore richer checkpoint data
including:

* Completed task hashes
* Partial progress of currently‑running tasks
* Learned patterns / model artefacts
* Engine performance statistics (timings, resource usage, etc.)

The checkpoint is stored as a JSON file (with optional binary blobs for large
objects) under a user‑specified location.  The format is versioned to allow
future extensions without breaking backward compatibility.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #

class EngineStats(TypedDict, total=False):
    """Performance statistics collected from the execution engine."""
    cpu_percent: float
    memory_mb: float
    elapsed_seconds: float
    gpu_utilization: Optional[float]  # May be None if no GPU


@dataclass
class Checkpoint:
    """Container for all checkpointable state."""
    version: int = 1
    timestamp: float = field(default_factory=time.time)
    completed_task_hashes: List[str] = field(default_factory=list)
    partial_progress: Dict[str, Any] = field(default_factory=dict)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    engine_stats: EngineStats = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the checkpoint to a JSON‑compatible dict."""
        data = asdict(self)
        # Ensure any non‑JSON‑serialisable objects are converted safely.
        # For now we simply rely on json.dumps to raise if something is not
        # serialisable; callers can pre‑process complex objects before assigning
        # them to the checkpoint fields.
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Checkpoint":
        """Create a Checkpoint instance from a dict (e.g. loaded from JSON)."""
        # Version handling – future versions can add migration logic here.
        version = data.get("version", 1)
        return Checkpoint(
            version=version,
            timestamp=data.get("timestamp", time.time()),
            completed_task_hashes=data.get("completed_task_hashes", []),
            partial_progress=data.get("partial_progress", {}),
            learned_patterns=data.get("learned_patterns", {}),
            engine_stats=data.get("engine_stats", {})
        )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def save_checkpoint(
    checkpoint: Checkpoint,
    file_path: str | os.PathLike,
    ensure_dir: bool = True,
) -> None:
    """Persist a checkpoint to disk.

    Args:
        checkpoint: The Checkpoint instance to persist.
        file_path: Destination file (will be overwritten if it exists).
        ensure_dir: If True, creates parent directories automatically.
    """
    path = Path(file_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON atomically to avoid corrupt files on crash.
    temp_path = path.with_suffix(".tmp")
    with temp_path.open("w", encoding="utf-8") as fp:
        json.dump(checkpoint.to_dict(), fp, indent=2, sort_keys=True, default=str)

    temp_path.replace(path)


def load_checkpoint(file_path: str | os.PathLike) -> Optional[Checkpoint]:
    """Load a checkpoint from disk.

    Returns None if the file does not exist or cannot be parsed.
    """
    path = Path(file_path)
    if not path.is_file():
        return None

    try:
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        return Checkpoint.from_dict(data)
    except Exception as exc:  # pragma: no cover – defensive fallback
        # In a production system we would log the exception; here we simply
        # return None to signal a failed load.
        return None


def update_completed_hashes(
    checkpoint: Checkpoint,
    new_hashes: List[str],
) -> None:
    """Append new task hashes to the checkpoint's completed list, avoiding duplicates."""
    existing = set(checkpoint.completed_task_hashes)
    for h in new_hashes:
        if h not in existing:
            checkpoint.completed_task_hashes.append(h)
            existing.add(h)


def merge_partial_progress(
    checkpoint: Checkpoint,
    task_id: str,
    progress_fragment: Dict[str, Any],
) -> None:
    """Merge a fragment of partial progress for a given task."""
    if task_id not in checkpoint.partial_progress:
        checkpoint.partial_progress[task_id] = progress_fragment
    else:
        # Deep merge – simple shallow update for now.
        checkpoint.partial_progress[task_id].update(progress_fragment)


def record_engine_stats(
    checkpoint: Checkpoint,
    stats: EngineStats,
) -> None:
    """Record the latest engine performance statistics."""
    checkpoint.engine_stats = stats


# --------------------------------------------------------------------------- #
# Convenience helpers for the swarm / executor
# --------------------------------------------------------------------------- #

def default_checkpoint_path() -> Path:
    """Standard location for the checkpoint within the experiment folder."""
    return Path(
        "experiments",
        "exp_20260204_031422_unified_session_108",
        "checkpoint.json"
    )


def save_default_checkpoint(checkpoint: Checkpoint) -> None:
    """Save checkpoint to the experiment's default location."""
    save_checkpoint(checkpoint, default_checkpoint_path())


def load_default_checkpoint() -> Optional[Checkpoint]:
    """Load checkpoint from the experiment's default location."""
    return load_checkpoint(default_checkpoint_path())


# --------------------------------------------------------------------------- #
# Example usage (not executed on import)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    # Quick sanity check when run as a script.
    cp = Checkpoint()
    update_completed_hashes(cp, ["hash1", "hash2"])
    merge_partial_progress(cp, "task-42", {"step": 3, "status": "in_progress"})
    record_engine_stats(cp, {"cpu_percent": 12.5, "memory_mb": 256.0, "elapsed_seconds": 42.0})
    save_default_checkpoint(cp)

    loaded = load_default_checkpoint()
    assert loaded is not None
    assert loaded.completed_task_hashes == ["hash1", "hash2"]
    print("Checkpoint round‑trip succeeded.")