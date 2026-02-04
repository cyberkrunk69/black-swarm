#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool.

- Scans the repository file tree.
- Reads recent git history (last N commits).
- Identifies affected subsystems (based on configurable path patterns).
- Estimates implementation complexity (lines changed, number of files, etc.).
- Flags high‑risk changes (large diffs, deletions, binary files, etc.).
- Emits a JSON summary that can be used to hydrate the Expert Node.

Usage:
    python gut_check_planner.py [--commits N] [--output FILE]

The script is deliberately lightweight and has no external dependencies.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Configuration – adjust as needed for your project structure
# ----------------------------------------------------------------------
# Simple mapping of path regexes to logical subsystem names.
SUBSYSTEM_PATTERNS = {
    r"^app/.*\.py$": "application_logic",
    r"^tests/.*\.py$": "test_suite",
    r"^docs/.*": "documentation",
    r"^setup\.py$": "packaging",
    r"^requirements\.txt$": "dependencies",
    # fallback for anything else
    r".*": "miscellaneous",
}

# Thresholds for risk flagging
MAX_LINES_CHANGED = 500          # above this -> high risk
MAX_FILES_CHANGED = 20           # above this -> high risk
MAX_BINARY_CHANGES = 5           # above this -> high risk


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def run_git_cmd(args: List[str]) -> str:
    """Run a git command and return its stdout as string."""
    result = subprocess.run(
        ["git"] + args,
        cwd=Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"Git command failed: {' '.join(args)}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def scan_file_tree(root: Path) -> List[Path]:
    """Return a list of all files under the given root (excluding .git)."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .git directory
        if ".git" in dirnames:
            dirnames.remove(".git")
        for fname in filenames:
            files.append(Path(dirpath) / fname)
    return files


def get_recent_commits(limit: int = 10) -> List[Dict]:
    """Return a list of dicts with commit hash and message for recent commits."""
    log_fmt = "%H%x1f%s%x1f%ae%x1f%ad"
    raw = run_git_cmd(["log", f"-n{limit}", f"--pretty=format:{log_fmt}"])
    commits = []
    for line in raw.split("\n"):
        parts = line.split("\x1f")
        if len(parts) != 4:
            continue
        commit_hash, subject, author_email, author_date = parts
        commits.append(
            {
                "hash": commit_hash,
                "subject": subject,
                "author_email": author_email,
                "author_date": author_date,
            }
        )
    return commits


def diff_stats_for_commit(commit_hash: str) -> Tuple[int, int, int, List[Tuple[str, int]]]:
    """
    Return (files_changed, insertions, deletions, list_of_(file, lines_changed)).
    """
    diff_output = run_git_cmd(
        ["show", "--numstat", "--format=", commit_hash]
    )  # each line: insertions\tdeletions\tfilename
    files_changed = 0
    total_insertions = 0
    total_deletions = 0
    file_changes = []

    for line in diff_output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ins, dels, fname = parts
        # Binary files are marked with '-'
        if ins == "-" or dels == "-":
            ins_num = dels_num = 0
            is_binary = True
        else:
            ins_num = int(ins)
            dels_num = int(dels)
            is_binary = False

        files_changed += 1
        total_insertions += ins_num
        total_deletions += dels_num
        lines_changed = ins_num + dels_num
        file_changes.append((fname, lines_changed, is_binary))

    return files_changed, total_insertions, total_deletions, file_changes


def map_path_to_subsystem(path: str) -> str:
    """Return subsystem name based on SUBSYSTEM_PATTERNS."""
    for pattern, name in SUBSYSTEM_PATTERNS.items():
        if re.match(pattern, path):
            return name
    return "unknown"


def aggregate_subsystem_impact(file_changes: List[Tuple[str, int, bool]]) -> Dict[str, Dict]:
    """Aggregate impact per subsystem."""
    impact = defaultdict(lambda: {"files": 0, "lines_changed": 0, "binary": 0})
    for fname, lines, is_binary in file_changes:
        subsystem = map_path_to_subsystem(fname)
        impact[subsystem]["files"] += 1
        impact[subsystem]["lines_changed"] += lines
        if is_binary:
            impact[subsystem]["binary"] += 1
    return impact


def estimate_complexity(total_lines: int, total_files: int) -> str:
    """Very rough complexity estimator."""
    if total_lines > 1000 or total_files > 50:
        return "high"
    if total_lines > 300 or total_files > 15:
        return "moderate"
    return "low"


def flag_risks(total_lines: int, total_files: int, binary_count: int) -> List[str]:
    """Return a list of risk flags based on thresholds."""
    risks = []
    if total_lines > MAX_LINES_CHANGED:
        risks.append(f"Large line change count ({total_lines} > {MAX_LINES_CHANGED})")
    if total_files > MAX_FILES_CHANGED:
        risks.append(f"Many files changed ({total_files} > {MAX_FILES_CHANGED})")
    if binary_count > MAX_BINARY_CHANGES:
        risks.append(f"Multiple binary file changes ({binary_count} > {MAX_BINARY_CHANGES})")
    return risks


# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Quick gut‑check planner")
    parser.add_argument(
        "--commits",
        type=int,
        default=10,
        help="Number of recent commits to analyze (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Write JSON summary to file instead of stdout",
    )
    args = parser.parse_args()

    # 1. Scan repository tree (for possible future extensions)
    repo_root = Path.cwd()
    all_files = scan_file_tree(repo_root)

    # 2. Gather recent commit info
    recent_commits = get_recent_commits(limit=args.commits)

    # 3. Collect diff stats across those commits
    total_files_changed = 0
    total_insertions = 0
    total_deletions = 0
    all_file_changes = []

    for commit in recent_commits:
        fc, ins, dels, file_changes = diff_stats_for_commit(commit["hash"])
        total_files_changed += fc
        total_insertions += ins
        total_deletions += dels
        all_file_changes.extend(file_changes)

    total_lines_changed = total_insertions + total_deletions
    binary_changes = sum(1 for _, _, is_bin in all_file_changes if is_bin)

    # 4. Subsystem impact aggregation
    subsystem_impact = aggregate_subsystem_impact(all_file_changes)

    # 5. Complexity estimate
    complexity = estimate_complexity(total_lines_changed, total_files_changed)

    # 6. Risk flags
    risks = flag_risks(total_lines_changed, total_files_changed, binary_changes)

    # 7. Build context summary JSON
    summary = {
        "repo_root": str(repo_root),
        "scanned_files_count": len(all_files),
        "analyzed_commits": recent_commits,
        "total_files_changed": total_files_changed,
        "total_lines_changed": total_lines_changed,
        "total_insertions": total_insertions,
        "total_deletions": total_deletions,
        "binary_file_changes": binary_changes,
        "subsystem_impact": subsystem_impact,
        "estimated_complexity": complexity,
        "risk_flags": risks,
    }

    json_output = json.dumps(summary, indent=2, default=dict)

    if args.output:
        Path(args.output).write_text(json_output, encoding="utf-8")
    else:
        print(json_output)


if __name__ == "__main__":
    main()