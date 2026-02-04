#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the unified session experiment.

Features:
- Scans the repository file tree.
- Reads recent git history (default last 10 commits).
- Identifies affected subsystems based on path heuristics.
- Estimates overall change complexity.
- Flags high‑risk keywords in changed files/commit messages.
- Emits a JSON summary suitable for hydrating the Expert Node.
"""

import os
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import List, Dict, Any

# --------------------------------------------------------------------------- #
# Configuration (tweak as needed)
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]   # /app
MAX_COMMITS = 10
RISK_KEYWORDS = {"security", "auth", "password", "payment", "encrypt", "token"}
SYSTEM_KEYWORDS = {
    "backend": {"api", "service", "models", "controllers"},
    "frontend": {"ui", "templates", "static", "react", "vue"},
    "data": {"db", "migration", "schema", "etl"},
    "infra": {"docker", "k8s", "terraform", "ci", "cd"},
    "utils": {"helpers", "common", "shared"},
}
COMPLEXITY_THRESHOLDS = {
    "low": 20,
    "medium": 100,
    "high": 500,
}
# --------------------------------------------------------------------------- #


def run_git_cmd(args: List[str]) -> str:
    """Run a git command in the repo root and return stdout."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_file_tree() -> List[str]:
    """Return a list of all files (relative to repo root) in the workspace."""
    files = []
    for root, _, filenames in os.walk(REPO_ROOT):
        for fname in filenames:
            # Skip hidden files and the .git directory
            if fname.startswith('.'):
                continue
            full_path = Path(root) / fname
            rel_path = full_path.relative_to(REPO_ROOT).as_posix()
            files.append(rel_path)
    return files


def get_recent_commits(limit: int = MAX_COMMITS) -> List[Dict[str, Any]]:
    """Fetch recent commit metadata using `git log`."""
    log_format = "%H%x1f%an%x1f%ae%x1f%ad%x1f%s"
    raw = run_git_cmd(["log", f"-n{limit}", f"--pretty=format:{log_format}"])
    commits = []
    for line in raw.splitlines():
        sha, author_name, author_email, date, subject = line.split("\x1f")
        commits.append(
            {
                "sha": sha,
                "author": {"name": author_name, "email": author_email},
                "date": date,
                "subject": subject,
            }
        )
    return commits


def get_changed_files(commit_range: str = f"-n{MAX_COMMITS}") -> List[Dict[str, Any]]:
    """
    Return a list of changed files with added/removed line counts.
    Uses `git diff --numstat` across the recent commit range.
    """
    diff_output = run_git_cmd(["diff", "--numstat", commit_range])
    changes = []
    for line in diff_output.splitlines():
        added, removed, path = line.split("\t")
        changes.append(
            {
                "path": path,
                "added": int(added) if added != "-" else 0,
                "removed": int(removed) if removed != "-" else 0,
            }
        )
    return changes


def identify_affected_systems(changed_files: List[Dict[str, Any]]) -> List[str]:
    """Map changed file paths to high‑level system categories."""
    system_counter = Counter()
    for entry in changed_files:
        path = entry["path"].lower()
        for system, keywords in SYSTEM_KEYWORDS.items():
            if any(kw in path for kw in keywords):
                system_counter[system] += 1
                break
        else:
            system_counter["misc"] += 1
    # Return sorted list by relevance
    return [sys for sys, _ in system_counter.most_common()]


def estimate_complexity(changed_files: List[Dict[str, Any]]) -> str:
    """Simple complexity estimate based on total line changes."""
    total_changes = sum(cf["added"] + cf["removed"] for cf in changed_files)
    if total_changes <= COMPLEXITY_THRESHOLDS["low"]:
        return "low"
    if total_changes <= COMPLEXITY_THRESHOLDS["medium"]:
        return "medium"
    if total_changes <= COMPLEXITY_THRESHOLDS["high"]:
        return "high"
    return "very high"


def flag_risks(changed_files: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> List[str]:
    """Detect high‑risk keywords in file paths or commit messages."""
    risks = set()
    # Check file paths
    for cf in changed_files:
        path = cf["path"].lower()
        for kw in RISK_KEYWORDS:
            if kw in path:
                risks.add(f"File path risk: '{kw}' in {cf['path']}")
    # Check commit subjects
    for cm in commits:
        subject = cm["subject"].lower()
        for kw in RISK_KEYWORDS:
            if kw in subject:
                risks.add(f"Commit message risk: '{kw}' in \"{cm['subject']}\"")
    return sorted(risks)


def main() -> None:
    try:
        file_tree = get_file_tree()
        commits = get_recent_commits()
        changed_files = get_changed_files()
        affected_systems = identify_affected_systems(changed_files)
        complexity = estimate_complexity(changed_files)
        risks = flag_risks(changed_files, commits)

        summary = {
            "file_tree": file_tree,
            "recent_commits": commits,
            "changed_files": changed_files,
            "affected_systems": affected_systems,
            "complexity_estimate": complexity,
            "risks": risks,
        }

        json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    except Exception as exc:
        sys.stderr.write(f"Error during gut check planning: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()