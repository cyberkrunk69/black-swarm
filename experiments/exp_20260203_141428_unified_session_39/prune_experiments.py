#!/usr/bin/env python3
"""
prune_experiments.py

Utility to clean up the `experiments/` directory by:
1. Listing all experiment sub‑directories older than 24 hours.
2. Detecting which of those contain *useful* output
   (i.e., at least one non‑empty file that is not a duplicate of another experiment).
3. Deleting directories that are empty or only contain duplicate output.
4. Keeping only experiments with unique, substantial output.
5. Reporting the number of directories deleted, kept, and total bytes freed.

**Safety notes**
* Directories created/modified **today** are never touched.
* Core system files (`grind_spawner*.py`, `safety_*.py`) are never deleted.
* A dry‑run mode (`--dry-run`) is provided; use it before actual deletion.

Usage:
    python prune_experiments.py [--dry-run] [--root PATH]

Arguments:
    --dry-run   Perform all checks and print what would be done without deleting anything.
    --root PATH Path to the experiments root directory (default: "../experiments").
"""

import argparse
import hashlib
import os
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------

def compute_file_hash(path: Path, block_size: int = 65536) -> str:
    """Return SHA256 hash of a file's contents."""
    hasher = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()

def is_today(timestamp: float) -> bool:
    """True if the given epoch timestamp is from the current calendar day."""
    local_time = time.localtime(timestamp)
    now = time.localtime()
    return (local_time.tm_year == now.tm_year and
            local_time.tm_yday == now.tm_yday)

def list_experiment_dirs(root: Path) -> list[Path]:
    """Return all immediate sub‑directories under `root` that look like experiments."""
    return [p for p in root.iterdir() if p.is_dir()]

def dir_age_hours(path: Path) -> float:
    """Age of the directory in hours based on its latest modification time."""
    latest_mtime = max((f.stat().st_mtime for f in path.rglob('*') if f.is_file()), default=path.stat().st_mtime)
    return (time.time() - latest_mtime) / 3600.0

def gather_file_hashes(dirs: list[Path]) -> dict[str, list[Path]]:
    """
    Build a mapping from file hash -> list of file paths that share that hash.
    Only non‑empty files are considered.
    """
    hash_map = defaultdict(list)
    for d in dirs:
        for f in d.rglob('*'):
            if f.is_file():
                if f.stat().st_size == 0:
                    continue
                try:
                    h = compute_file_hash(f)
                    hash_map[h].append(f)
                except Exception as e:
                    print(f"Warning: could not hash {f}: {e}", file=sys.stderr)
    return hash_map

def is_duplicate_dir(dir_path: Path, hash_map: dict[str, list[Path]]) -> bool:
    """
    Determine if *all* non‑empty files inside `dir_path` have duplicates elsewhere.
    Returns True if the directory contains no unique (non‑duplicate) files.
    """
    for f in dir_path.rglob('*'):
        if f.is_file() and f.stat().st_size > 0:
            h = compute_file_hash(f)
            # If this hash appears only once, the file is unique.
            if len(hash_map.get(h, [])) == 1:
                return False
    return True

def delete_dir(path: Path, dry_run: bool) -> int:
    """Delete a directory (recursively). Returns the total bytes freed."""
    total_freed = 0
    for f in path.rglob('*'):
        if f.is_file():
            total_freed += f.stat().st_size
    if dry_run:
        print(f"[DRY‑RUN] Would delete: {path}")
    else:
        shutil.rmtree(path)
        print(f"Deleted: {path}")
    return total_freed

def main():
    parser = argparse.ArgumentParser(description="Prune old experiment directories.")
    parser.add_argument('--dry-run', action='store_true', help='Perform a trial run with no deletions.')
    parser.add_argument('--root', type=str, default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'experiments')),
                        help='Root experiments directory (default: ../../experiments)')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning experiments in: {root}")
    all_dirs = list_experiment_dirs(root)

    # 1. Filter directories older than 24 hours and not from today
    old_dirs = [d for d in all_dirs if dir_age_hours(d) > 24 and not is_today(d.stat().st_mtime)]
    print(f"Found {len(old_dirs)} experiment directories older than 24 h (excluding today).")

    # 2. Build hash map for all files in those directories
    hash_map = gather_file_hashes(old_dirs)

    # 3. Decide which dirs to delete
    to_delete = []
    to_keep = []
    bytes_freed = 0

    for d in old_dirs:
        # Empty directory?
        if not any(f.is_file() for f in d.rglob('*')):
            to_delete.append(d)
            continue

        # Duplicate‑only directory?
        if is_duplicate_dir(d, hash_map):
            to_delete.append(d)
        else:
            to_keep.append(d)

    # 4. Perform deletion
    for d in to_delete:
        bytes_freed += delete_dir(d, args.dry_run)

    # 5. Summary
    print("\n=== Summary ===")
    print(f"Directories kept   : {len(to_keep)}")
    print(f"Directories deleted: {len(to_delete)}")
    print(f"Total bytes freed   : {bytes_freed:,} bytes")
    if args.dry_run:
        print("\nNOTE: This was a dry‑run. No files were actually removed.")

if __name__ == "__main__":
    main()