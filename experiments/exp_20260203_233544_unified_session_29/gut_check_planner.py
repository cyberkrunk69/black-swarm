#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the current repository.

Features:
- Scans the file tree under the workspace root.
- Reads recent git history (last N commits).
- Identifies "affected systems" by simple heuristics (e.g., top‑level directories).
- Estimates complexity (lines changed, number of files touched).
- Flags obvious risks (large diffs, many files, binary changes).

The script emits a JSON document to STDOUT that can be used to
hydrate the Expert Node in the orchestration pipeline.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Configuration (tweak as needed)
# ----------------------------------------------------------------------
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]   # D:\codingProjects\claude_parasite_brain_suck
GIT_CMD = "git"
MAX_COMMITS = 20            # How many recent commits to inspect
LINE_CHANGE_THRESHOLD = 500  # Flag if total added/removed lines exceed this
FILE_CHANGE_THRESHOLD = 30   # Flag if more than this many files changed
BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe", ".dll"}

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def run_git(args: List[str]) -> str:
    """Run a git command inside the workspace and return its stdout."""
    result = subprocess.run(
        [GIT_CMD] + args,
        cwd=str(WORKSPACE_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()

def get_recent_commits(limit: int = MAX_COMMITS) -> List[Dict[str, Any]]:
    """Return a list of recent commit dicts with hash, author, date, and message."""
    log_fmt = "%H%x1f%an%x1f%ad%x1f%s"
    raw = run_git(["log", f"-{limit}", f"--pretty=format:{log_fmt}", "--date=iso"])
    commits = []
    for line in raw.splitlines():
        sha, author, date, subject = line.split("\x1f")
        commits.append({
            "sha": sha,
            "author": author,
            "date": date,
            "message": subject,
        })
    return commits

def get_diff_stats(commit_sha: str) -> Dict[str, Any]:
    """Return diff stats for a given commit."""
    raw = run_git(["show", "--numstat", "--format=", commit_sha])
    added = 0
    removed = 0
    files = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add_str, del_str, filename = parts
        # Handle binary files (add_str/del_str are "-")
        if add_str == "-" or del_str == "-":
            is_binary = True
            add = del_ = 0
        else:
            is_binary = False
            add = int(add_str)
            del_ = int(del_str)

        added += add
        removed += del_
        files.append({
            "path": filename,
            "added": add,
            "removed": del_,
            "binary": is_binary,
        })
    return {
        "added_lines": added,
        "removed_lines": removed,
        "total_files": len(files),
        "files": files,
    }

def scan_file_tree(root: Path) -> List[str]:
    """Return a list of all file paths (relative to workspace) under root."""
    all_files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            rel_path = os.path.relpath(os.path.join(dirpath, f), start=root)
            all_files.append(rel_path.replace("\\", "/"))
    return all_files

def infer_affected_systems(files: List[Dict[str, Any]]) -> List[str]:
    """Simple heuristic: top‑level directory names are considered systems."""
    systems = set()
    for f in files:
        parts = f["path"].split("/")
        if len(parts) > 1:
            systems.add(parts[0])
    return sorted(systems)

def flag_risks(diff: Dict[str, Any]) -> List[str]:
    """Generate risk flags based on diff statistics."""
    risks = []
    total_changes = diff["added_lines"] + diff["removed_lines"]
    if total_changes > LINE_CHANGE_THRESHOLD:
        risks.append(f"Large line change count ({total_changes} lines)")

    if diff["total_files"] > FILE_CHANGE_THRESHOLD:
        risks.append(f"Many files changed ({diff['total_files']} files)")

    binary_files = [f["path"] for f in diff["files"] if f["binary"]]
    if binary_files:
        risks.append(f"Binary files modified: {', '.join(binary_files)}")

    return risks

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    # 1. Gather recent commit info
    commits = get_recent_commits()
    if not commits:
        print(json.dumps({"error": "No commits found"}))
        sys.exit(0)

    # 2. Aggregate diff stats across the selected commits
    aggregate = {
        "added_lines": 0,
        "removed_lines": 0,
        "total_files": 0,
        "files": [],
    }
    for c in commits:
        stats = get_diff_stats(c["sha"])
        aggregate["added_lines"] += stats["added_lines"]
        aggregate["removed_lines"] += stats["removed_lines"]
        aggregate["total_files"] += stats["total_files"]
        aggregate["files"].extend(stats["files"])

    # 3. Identify affected systems
    affected_systems = infer_affected_systems(aggregate["files"])

    # 4. Compute risk flags
    risks = flag_risks(aggregate)

    # 5. Scan the whole workspace (lightweight)
    all_files = scan_file_tree(WORKSPACE_ROOT)

    # 6. Build the context summary
    context = {
        "workspace_root": str(WORKSPACE_ROOT),
        "recent_commits": commits,
        "diff_summary": {
            "added_lines": aggregate["added_lines"],
            "removed_lines": aggregate["removed_lines"],
            "total_files_changed": aggregate["total_files"],
        },
        "affected_systems": affected_systems,
        "risk_flags": risks,
        "file_tree_snapshot": all_files,   # optional, can be trimmed by consumer
    }

    # Output JSON
    json.dump(context, sys.stdout, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()