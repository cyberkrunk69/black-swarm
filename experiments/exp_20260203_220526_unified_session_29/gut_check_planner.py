#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the current workspace.

Features:
- Scans the file tree (excluding .git and other ignored patterns).
- Reads recent git history (last N commits).
- Identifies potentially affected subsystems based on path heuristics.
- Estimates a simple complexity score.
- Flags high‑risk changes.
- Emits a JSON context summary that can be used to hydrate an Expert Node.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DEFAULT_COMMIT_COUNT = 20
IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.venv'}
SUBSYSTEM_KEYWORDS = {
    'core': ['core', 'engine', 'kernel'],
    'api': ['api', 'service', 'endpoint'],
    'ui': ['ui', 'frontend', 'static', 'templates'],
    'db': ['db', 'database', 'model', 'schema'],
    'tests': ['test', 'tests'],
    'cli': ['cli', 'command'],
    'infra': ['docker', 'k8s', 'infra', 'deployment'],
}
RISK_LINE_THRESHOLD = 500   # lines added/removed considered high risk
RISK_FILE_COUNT_THRESHOLD = 30  # number of files changed considered high risk

# --------------------------------------------------------------------------- #
# Helper Functions
# --------------------------------------------------------------------------- #

def run_git_cmd(args: List[str], cwd: Path) -> str:
    """Run a git command and return its stdout."""
    result = subprocess.run(
        ['git'] + args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()

def get_recent_commits(repo_path: Path, count: int = DEFAULT_COMMIT_COUNT) -> List[Dict[str, Any]]:
    """Return a list of recent commits with basic metadata."""
    log_format = "%H%x1f%an%x1f%ad%x1f%s"
    raw = run_git_cmd(
        ['log', f'-n{count}', f'--pretty=format:{log_format}', '--date=iso'],
        cwd=repo_path,
    )
    commits = []
    for line in raw.splitlines():
        sha, author, date_str, message = line.split('\x1f')
        commits.append({
            "sha": sha,
            "author": author,
            "date": date_str,
            "message": message,
        })
    return commits

def scan_file_tree(root: Path) -> List[Path]:
    """Recursively list all files under root, respecting IGNORE_DIRS."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignored directories in‑place
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith('.')]
        for fname in filenames:
            if fname.startswith('.'):
                continue
            files.append(Path(dirpath) / fname)
    return files

def infer_affected_systems(changed_paths: List[Path]) -> List[str]:
    """Simple heuristic: match path components against SUBSYSTEM_KEYWORDS."""
    hits = Counter()
    for p in changed_paths:
        parts = [part.lower() for part in p.parts]
        for system, keywords in SUBSYSTEM_KEYWORDS.items():
            if any(kw in part for part in parts for kw in keywords):
                hits[system] += 1
    # Return sorted list of systems by occurrence count
    return [system for system, _ in hits.most_common()]

def compute_complexity(changed_files: List[Path], commit_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Estimate complexity based on file count and line changes."""
    total_files = len(changed_files)
    total_add = sum(int(c.get('added', 0)) for c in commit_stats)
    total_del = sum(int(c.get('deleted', 0)) for c in commit_stats)
    score = total_files * 0.5 + (total_add + total_del) * 0.001
    return {
        "files_changed": total_files,
        "lines_added": total_add,
        "lines_deleted": total_del,
        "complexity_score": round(score, 3),
    }

def gather_commit_file_stats(repo_path: Path, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """For each commit, collect added/deleted line counts and touched files."""
    stats = []
    for c in commits:
        diff = run_git_cmd(['show', '--numstat', '--format=', c['sha']], cwd=repo_path)
        added = deleted = 0
        files = []
        for line in diff.splitlines():
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            add_str, del_str, file_path = parts
            # Git may output '-' for binary files; treat as 0
            add = int(add_str) if add_str.isdigit() else 0
            delete = int(del_str) if del_str.isdigit() else 0
            added += add
            deleted += delete
            files.append(Path(file_path))
        stats.append({
            "sha": c['sha'],
            "added": added,
            "deleted": deleted,
            "files": files,
        })
    return stats

def flag_risks(complexity: Dict[str, Any]) -> List[str]:
    """Generate risk flags based on thresholds."""
    flags = []
    if complexity["lines_added"] + complexity["lines_deleted"] > RISK_LINE_THRESHOLD:
        flags.append("high_line_change")
    if complexity["files_changed"] > RISK_FILE_COUNT_THRESHOLD:
        flags.append("many_files_changed")
    return flags

# --------------------------------------------------------------------------- #
# Main Execution
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Quick gut‑check analysis for the workspace."
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="Path to the git repository (default: current working directory).",
    )
    parser.add_argument(
        "--commits",
        type=int,
        default=DEFAULT_COMMIT_COUNT,
        help="Number of recent commits to analyze.",
    )
    args = parser.parse_args()

    repo_path = args.repo.resolve()
    if not (repo_path / ".git").exists():
        sys.exit("Error: Provided path does not appear to be a git repository.")

    # 1. Scan file tree
    all_files = scan_file_tree(repo_path)

    # 2. Get recent commit metadata
    recent_commits = get_recent_commits(repo_path, count=args.commits)

    # 3. Gather per‑commit file/line stats
    commit_stats = gather_commit_file_stats(repo_path, recent_commits)

    # 4. Consolidate changed files across the examined commits
    changed_files = set()
    for cs in commit_stats:
        changed_files.update(cs["files"])
    changed_files = list(changed_files)

    # 5. Identify affected subsystems
    affected_systems = infer_affected_systems(changed_files)

    # 6. Compute complexity estimate
    complexity = compute_complexity(changed_files, commit_stats)

    # 7. Determine risk flags
    risk_flags = flag_risks(complexity)

    # 8. Build context summary
    summary = {
        "workspace_root": str(repo_path),
        "files_scanned": len(all_files),
        "recent_commits": recent_commits,
        "changed_files": [str(p) for p in changed_files],
        "affected_systems": affected_systems,
        "complexity": complexity,
        "risk_flags": risk_flags,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    # Output JSON to stdout (pretty‑printed)
    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")

if __name__ == "__main__":
    main()