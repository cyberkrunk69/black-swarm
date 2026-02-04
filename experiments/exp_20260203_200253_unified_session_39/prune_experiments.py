#!/usr/bin/env python3
import os
import hashlib
import shutil
import time
from pathlib import Path

BASE_DIR = Path("/app/experiments")
NOW = time.time()
ONE_DAY = 24 * 60 * 60

def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def dir_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total

def main():
    # 1. List all experiments older than 24 hours
    old_exps = []
    for entry in BASE_DIR.iterdir():
        if entry.is_dir():
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            if NOW - mtime > ONE_DAY:
                old_exps.append(entry)

    # 2. Check which have useful output (non‑empty, non‑duplicate)
    # We'll keep a map of hash -> (path, size) for first occurrence
    seen_hashes = {}
    kept = []
    deleted = []
    freed_bytes = 0

    for exp in sorted(old_exps, key=lambda p: p.stat().st_mtime):
        # Gather all files in this experiment
        file_paths = [p for p in exp.rglob("*") if p.is_file()]
        if not file_paths:
            # empty directory -> delete
            size = dir_size(exp)
            shutil.rmtree(exp)
            deleted.append(exp.name)
            freed_bytes += size
            continue

        # Determine if any file is new (unique)
        has_unique = False
        duplicate_hashes = []
        for f in file_paths:
            try:
                h = file_hash(f)
            except OSError:
                continue
            if h not in seen_hashes:
                has_unique = True
                seen_hashes[h] = (f, f.stat().st_size)
            else:
                duplicate_hashes.append(h)

        if has_unique:
            # keep this experiment
            kept.append(exp.name)
        else:
            # all files are duplicates of already‑kept content -> delete
            size = dir_size(exp)
            shutil.rmtree(exp)
            deleted.append(exp.name)
            freed_bytes += size

    # 5. Report
    print(f"Deleted: {len(deleted)} experiment(s)")
    print(f"Kept: {len(kept)} experiment(s)")
    print(f"Bytes freed: {freed_bytes}")

if __name__ == "__main__":
    main()