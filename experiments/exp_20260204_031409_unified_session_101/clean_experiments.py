#!/usr/bin/env python3
"""
clean_experiments.py

Utility to clean up the `experiments/` directory after successful integration.
- Archives or deletes experiments that have been merged.
- Retains failed experiments for further analysis.
- Updates the manifest with integration timestamps.

Usage:
    python clean_experiments.py
"""

import os
import json
import shutil
import zipfile
from datetime import datetime, timezone

EXPERIMENTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "manifest.json")
ARCHIVE_DIR = os.path.join(EXPERIMENTS_ROOT, "archive")

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"integrated_experiments": [], "failed_experiments": [], "last_cleanup": None}

def save_manifest(manifest):
    manifest["last_cleanup"] = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, sort_keys=True)

def get_experiment_status(exp_path):
    """
    Determine the status of an experiment.
    Expected: a file named `status.txt` containing either 'merged' or 'failed'.
    """
    status_file = os.path.join(exp_path, "status.txt")
    if not os.path.isfile(status_file):
        return None
    with open(status_file, "r", encoding="utf-8") as f:
        return f.read().strip().lower()

def archive_experiment(exp_path, exp_name):
    """
    Archive the experiment directory into a zip file under ARCHIVE_DIR.
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archive_path = os.path.join(ARCHIVE_DIR, f"{exp_name}.zip")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(exp_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, exp_path)
                zipf.write(full_path, arcname=rel_path)

def clean_experiments():
    manifest = load_manifest()
    now_iso = datetime.now(timezone.utc).isoformat()

    for entry in os.scandir(EXPERIMENTS_ROOT):
        if not entry.is_dir():
            continue
        if entry.name.startswith("exp_"):
            exp_path = entry.path
            exp_name = entry.name
            status = get_experiment_status(exp_path)

            if status == "merged":
                # Archive then delete
                archive_experiment(exp_path, exp_name)
                shutil.rmtree(exp_path)
                manifest["integrated_experiments"].append({
                    "experiment_id": exp_name,
                    "integrated_at": now_iso,
                    "status": "merged"
                })
                print(f"[INFO] Archived and removed merged experiment: {exp_name}")

            elif status == "failed":
                # Keep for analysis, just record in manifest if not already present
                if not any(e["experiment_id"] == exp_name for e in manifest["failed_experiments"]):
                    manifest["failed_experiments"].append({
                        "experiment_id": exp_name,
                        "detected_at": now_iso,
                        "status": "failed"
                    })
                print(f"[INFO] Retained failed experiment: {exp_name}")

            else:
                # Unknown or missing status; skip
                print(f"[WARN] Skipping experiment with unknown status: {exp_name}")

    save_manifest(manifest)
    print("[INFO] Cleanup complete. Manifest updated.")

if __name__ == "__main__":
    clean_experiments()