\"\"\"checkpoint_manager.py
Rich checkpointing utilities for the swarm execution framework.

Features
--------
* Persists completed task hashes.
* Persists partial progress of in‑flight tasks.
* Persists learned patterns (e.g., regexes, heuristics).
* Persists engine performance statistics (timings, resource usage).

Usage
-----
>>> from checkpoint_manager import CheckpointManager
>>> cp = CheckpointManager()
>>> cp.update_completed(task_hash='abc123')
>>> cp.update_partial(task_id='t42', progress=0.6, data={'partial': 'result'})
>>> cp.update_pattern(name='email_extractor', pattern=r'[\\w.-]+@[\\w.-]+')
>>> cp.update_perf(metric='cpu_time', value=12.34)
>>> cp.save()  # writes to default location
>>> cp2 = CheckpointManager.load()  # restores state
\"\"\"

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CHECKPOINT_DIR = Path(__file__).parent
DEFAULT_CHECKPOINT_FILE = DEFAULT_CHECKPOINT_DIR / "checkpoint.json"
_LOCK = threading.Lock()


@dataclass
class CheckpointState:
    \"\"\"Container for all checkpointable data.\"
    completed_hashes: List[str] = field(default_factory=list)
    partial_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    learned_patterns: Dict[str, str] = field(default_factory=dict)
    performance_stats: Dict[str, Any] = field(default_factory=dict)


class CheckpointManager:
    \"\"\"Manage saving/loading of checkpoint data.\n\n    The manager is thread‑safe and stores data in a JSON file.  JSON is chosen for\n    human readability and easy merging across restarts.\n    \"\"\"

    def __init__(self, checkpoint_path: Optional[Path] = None):
        self.path = checkpoint_path or DEFAULT_CHECKPOINT_FILE
        self.state = CheckpointState()
        # Attempt to load existing checkpoint silently
        if self.path.is_file():
            try:
                self.load()
            except Exception as exc:  # pragma: no cover
                # Corrupt checkpoint – start fresh but keep the file for debugging
                print(f\"[CheckpointManager] Warning: failed to load existing checkpoint: {exc}\")

    # --------------------------------------------------------------------- #
    #  Update helpers
    # --------------------------------------------------------------------- #
    def update_completed(self, task_hash: str) -> None:
        \"\"\"Record a completed task hash.\"
        with _LOCK:
            if task_hash not in self.state.completed_hashes:
                self.state.completed_hashes.append(task_hash)

    def update_partial(self, task_id: str, progress: float, data: Optional[Dict[str, Any]] = None) -> None:
        \"\"\"Record partial progress for a task.\n\n        ``progress`` should be a float in ``[0.0, 1.0]``.\n        ``data`` can hold any serialisable auxiliary information.\n        \"\"\"
        with _LOCK:
            entry = {
                \"progress\": max(0.0, min(1.0, progress)),
                \"data\": data or {}
            }
            self.state.partial_progress[task_id] = entry

    def update_pattern(self, name: str, pattern: str) -> None:
        \"\"\"Store a learned pattern (e.g., regex) under a human‑readable name.\"\"\"
        with _LOCK:
            self.state.learned_patterns[name] = pattern

    def update_perf(self, metric: str, value: Any) -> None:
        \"\"\"Add or update a performance metric.\n\n        ``value`` must be JSON‑serialisable.\n        \"\"\"
        with _LOCK:
            self.state.performance_stats[metric] = value

    # --------------------------------------------------------------------- #
    #  Persistence
    # --------------------------------------------------------------------- #
    def save(self, path: Optional[Path] = None) -> None:
        \"\"\"Serialise the current state to ``self.path`` (or ``path`` if supplied).\"\"\"
        target = path or self.path
        target.parent.mkdir(parents=True, exist_ok=True)
        with _LOCK, target.open('w', encoding='utf-8') as fp:
            json.dump(asdict(self.state), fp, indent=2, sort_keys=True)
        # Ensure data is flushed to disk
        os.fsync(fp.fileno())

    def load(self, path: Optional[Path] = None) -> None:
        \"\"\"Load checkpoint data from ``self.path`` (or ``path`` if supplied).\"\"\"
        source = path or self.path
        if not source.is_file():
            raise FileNotFoundError(f\"Checkpoint file not found: {source}\")
        with _LOCK, source.open('r', encoding='utf-8') as fp:
            raw = json.load(fp)
        # Defensive reconstruction – ignore unknown keys
        self.state = CheckpointState(
            completed_hashes=raw.get('completed_hashes', []),
            partial_progress=raw.get('partial_progress', {}),
            learned_patterns=raw.get('learned_patterns', {}),
            performance_stats=raw.get('performance_stats', {})
        )

    # --------------------------------------------------------------------- #
    #  Convenience accessors
    # --------------------------------------------------------------------- #
    def get_completed(self) -> List[str]:
        return list(self.state.completed_hashes)

    def get_partial(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.state.partial_progress.get(task_id)

    def get_pattern(self, name: str) -> Optional[str]:
        return self.state.learned_patterns.get(name)

    def get_perf(self, metric: str) -> Optional[Any]:
        return self.state.performance_stats.get(metric)

    # --------------------------------------------------------------------- #
    #  Class helpers
    # --------------------------------------------------------------------- #
    @classmethod
    def load_latest(cls, checkpoint_dir: Optional[Path] = None) -> \"CheckpointManager\":
        \"\"\"Factory that loads the most recent checkpoint in ``checkpoint_dir``.\n\n        If no checkpoint exists, a fresh manager is returned.\n        \"\"\"
        dir_path = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
        candidate = dir_path / \"checkpoint.json\"
        manager = cls(candidate)
        return manager