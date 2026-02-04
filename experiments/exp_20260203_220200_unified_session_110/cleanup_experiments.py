#!/usr/bin/env python3
"""
cleanup_experiments.py

Utility to keep the `experiments/` directory from growing unbounded.
- Archives merged experiments (moves them to `experiments/archive/`).
- Deletes only those that have already been archived.
- Retains failed experiments for further analysis.
- Updates the manifest with the cleanup timestamp.

Usage:
    python cleanup_experiments.py
"""

import json
import os
import shutil
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments")
ARCHIVE_DIR = os.path.join(EXPERIMENTS_DIR, "archive")
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "manifest.json")


def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {"integrated_experiments": []}
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest):
    manifest["last_cleanup"] = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)


def ensure_archive_dir():
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def archive_experiment(exp_path, exp_name):
    dest_path = os.path.join(ARCHIVE_DIR, exp_name)
    if os.path.isdir(dest_path) or os.path.isfile(dest_path):
        # Already archived
        return
    shutil.move(exp_path, dest_path)
    print(f"Archived: {exp_name}")


def cleanup():
    manifest = load_manifest()
    ensure_archive_dir()

    for entry in manifest.get("integrated_experiments", []):
        exp_id = entry.get("experiment_id")
        status = entry.get("status")
        exp_path = os.path.join(EXPERIMENTS_DIR, exp_id)

        if not os.path.exists(exp_path):
            # Already moved or removed
            continue

        if status == "merged":
            archive_experiment(exp_path, exp_id)
        elif status == "failed":
            # Keep for analysis
            print(f"Retaining failed experiment: {exp_id}")

    save_manifest(manifest)
    print("Cleanup complete. Manifest updated.")


if __name__ == "__main__":
    cleanup()