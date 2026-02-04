```python
#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the current workspace.

Features:
- Scans the repository file tree.
- Extracts recent Git history (default last 10 commits).
- Identifies "affected systems" based on top‑level directories.
- Estimates a simple complexity metric.
- Flags common risk indicators.

The script prints a JSON document to stdout.  The JSON structure is designed
to be consumed directly by the Expert Node ("hydrated") in downstream
processing.

Usage:
    python gut_check_planner.py [--commits N] [--root PATH]

"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def run_git_cmd(args: List[str], cwd: Path) -> str:
    """Run a git command and return its stdout as a string."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_git_root(start_path: Path) -> Path | None:
    """Find the repository root (the directory containing .git)."""
    try:
        out = run_git_cmd(["rev-parse", "--show-toplevel"], start_path)
        return Path(out) if out else None
    except Exception:
        return None


def recent_commits(repo_path: Path, n: int = 10) -> List[Dict]:
    """Return a list of dictionaries describing the last *n* commits."""
    raw = run_git_cmd(
        ["log", f"-n{n}", "--pretty=format:%H%x1f%an%x1f%ad%x1f%s", "--date=iso"], repo_path
    )
    commits = []
    for line in raw.splitlines():
        if not line:
            continue
        sha, author, date, subject = line.split("\x1f")
        commits.append(
            {"sha": sha, "author": author, "date": date, "subject": subject}
        )
    return commits


def changed_files_in_commits(repo_path: Path, commits: List[Dict]) -> List[Tuple[str, int, int]]:
    """
    For each commit, retrieve changed files with insert/delete counts.
    Returns a list of (filename, insertions, deletions).
    """
    changes = []
    for commit in commits:
        diff = run_git_cmd(
            ["show", "--numstat", "--format=", commit["sha"]], repo_path
        )
        for line in diff.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            ins, dels, filename = parts
            # Git uses '-' for binary files; treat as unknown size.
            try:
                ins_i = int(ins)
                dels_i = int(dels)
            except ValueError:
                ins_i = dels_i = -1
            changes.append((filename, ins_i, dels_i))
    return changes


def scan_file_tree(root: Path) -> List[Path]:
    """Return a list of all files under *root* (excluding .git)."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .git directory
        if ".git" in dirnames:
            dirnames.remove(".git")
        for name in filenames:
            files.append(Path(dirpath) / name)
    return files


def identify_affected_systems(changed_files: List[Tuple[str, int, int]]) -> List[str]:
    """
    Very naive heuristic: top‑level directory name is considered a system.
    Returns a deduplicated list.
    """
    systems = set()
    for filename, _, _ in changed_files:
        parts = Path(filename).parts
        if len(parts) > 1:
            systems.add(parts[0])
    return sorted(systems)


def estimate_complexity(changed_files: List[Tuple[str, int, int]]) -> Dict:
    """
    Simple complexity estimate:
        - total files touched
        - total insertions / deletions
        - average change per file
    """
    total_files = len({f for f, _, _ in changed_files})
    total_ins = sum(ins for _, ins, _ in changed_files if ins >= 0)
    total_dels = sum(dels for _, _, dels in changed_files if dels >= 0)

    avg_ins = total_ins / total_files if total_files else 0
    avg_dels = total_dels / total_files if total_files else 0

    return {
        "total_files_changed": total_files,
        "total_insertions": total_ins,
        "total_deletions": total_dels,
        "average_insertions_per_file": round(avg_ins, 2),
        "average_deletions_per_file": round(avg_dels, 2),
    }


def flag_risks(changed_files: List[Tuple[str, int, int]]) -> List[str]:
    """
    Flag common risk patterns:
        - Binary files touched
        - Large file modifications (> 500 lines)
        - Deletion of many lines (> 300)
    """
    risks = []
    for filename, ins, dels in changed_files:
        if ins == -1 or dels == -1:
            risks.append(f"Binary or non‑text file modified: {filename}")
            continue
        if ins + dels > 500:
            risks.append(f"Large change ({ins}+{dels} lines) in {filename}")
        if dels > 300:
            risks.append(f"Massive deletions ({dels} lines) in {filename}")
    return risks


# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def generate_summary(root: Path, commit_limit: int = 10) -> Dict:
    repo_root = get_git_root(root) or root
    commits = recent_commits(repo_root, n=commit_limit)
    changed = changed_files_in_commits(repo_root, commits)

    summary = {
        "repo_root": str(repo_root),
        "scanned_at": Path.cwd().as_posix(),
        "recent_commits": commits,
        "affected_systems": identify_affected_systems(changed),
        "complexity_estimate": estimate_complexity(changed),
        "risk_flags": flag_risks(changed),
        "total_files_in_repo": len(scan_file_tree(repo_root)),
    }
    return summary


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Quick gut‑check analysis for the current workspace."
    )
    parser.add_argument(
        "--commits",
        type=int,
        default=10,
        help="Number of recent commits to analyse (default: 10)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Path to start scanning (defaults to current working directory)",
    )
    args = parser.parse_args(argv)

    summary = generate_summary(args.root, commit_limit=args.commits)
    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```