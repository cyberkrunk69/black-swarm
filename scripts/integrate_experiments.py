#!/usr/bin/env python3
"""
Self‑integration pipeline for experimental code.

This script scans the `experiments/` directory for files that have a counterpart
in the main codebase (e.g., `dashboard_vision.js`). For each matching file it:

1. Copies the experimental version over the main file.
2. Runs the project's test suite (`npm test`). If tests fail, the change is
   reverted and reported.
3. If tests pass, creates a dedicated git branch, commits the change, and merges
   it into `main` (fast‑forward or via a merge commit if needed).

Usage:
    python scripts/integrate_experiments.py
"""

import os
import subprocess
import sys
import datetime
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = ROOT_DIR / "experiments"
MAIN_DIR = ROOT_DIR

def run_cmd(cmd, cwd=ROOT_DIR, capture_output=False):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\nOutput:\n{result.stdout}")
    return result.stdout if capture_output else ""

def find_matching_files():
    matches = []
    for exp_path in EXPERIMENTS_DIR.rglob("*.*"):
        rel_path = exp_path.relative_to(EXPERIMENTS_DIR)
        target_path = MAIN_DIR / rel_path
        if target_path.is_file():
            matches.append((exp_path, target_path))
    return matches

def backup_file(path):
    backup_path = path.with_suffix(path.suffix + ".bak")
    shutil.copy2(path, backup_path)
    return backup_path

def restore_backup(backup_path, original_path):
    shutil.move(str(backup_path), str(original_path))

def integrate_file(exp_path, target_path):
    print(f"Integrating {exp_path} → {target_path}")
    backup = backup_file(target_path)
    try:
        shutil.copy2(exp_path, target_path)
        # Run tests
        print("Running test suite...")
        run_cmd("npm test")
    except Exception as e:
        print(f"Error during integration of {target_path}: {e}")
        print("Reverting changes...")
        restore_backup(backup, target_path)
        raise
    else:
        # Tests passed, clean backup
        os.remove(backup)

def git_commit_and_merge(changed_files):
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    branch_name = f"integration/{timestamp}"
    print(f"Creating branch {branch_name}")
    run_cmd(f"git checkout -b {branch_name}")

    files_str = " ".join(str(p.relative_to(ROOT_DIR)) for p in changed_files)
    run_cmd(f"git add {files_str}")
    run_cmd(f'git commit -m "Integrate experimental changes ({timestamp})"')

    # Switch back to main and merge
    run_cmd("git checkout main")
    # Fast‑forward if possible, otherwise create a merge commit
    try:
        run_cmd(f"git merge --ff-only {branch_name}")
    except RuntimeError:
        run_cmd(f"git merge --no-ff {branch_name}")

    # Clean up branch
    run_cmd(f"git branch -d {branch_name}")

def main():
    matches = find_matching_files()
    if not matches:
        print("No matching experimental files found.")
        return

    changed = []
    for exp_path, target_path in matches:
        try:
            integrate_file(exp_path, target_path)
            changed.append(target_path)
        except Exception:
            print("Aborting integration due to errors.")
            sys.exit(1)

    if changed:
        git_commit_and_merge(changed)
        print("Integration complete and merged into main.")
    else:
        print("No files were changed.")

if __name__ == "__main__":
    main()
```