#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the unified session experiment.

- Scans the repository file tree.
- Reads recent git history.
- Identifies potentially affected subsystems.
- Estimates implementation complexity.
- Flags obvious risk factors.

Outputs a JSON summary that can be used to HYDRATE the Expert Node.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def scan_file_tree(root: Path) -> List[str]:
    """Return a list of relative file paths under the given root."""
    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            # Skip hidden files and the analysis script itself
            if f.startswith('.'):
                continue
            rel_path = os.path.relpath(os.path.join(dirpath, f), root)
            files.append(rel_path)
    return files


def get_recent_git_commits(limit: int = 10) -> List[Dict[str, Any]]:
    """Return a list of recent git commit dicts (hash, author, date, message)."""
    try:
        raw = subprocess.check_output(
            ["git", "log", f"-n{limit}", "--pretty=format:%H%x1f%an%x1f%ad%x1f%s", "--date=short"],
            text=True,
        )
        commits = []
        for line in raw.strip().split("\n"):
            if not line:
                continue
            sha, author, date, message = line.split("\x1f")
            commits.append(
                {"sha": sha, "author": author, "date": date, "message": message}
            )
        return commits
    except Exception:
        # Not a git repo or git unavailable
        return []


def identify_affected_systems(files: List[str]) -> List[str]:
    """
    Very naive mapping of file paths to high‑level subsystems.
    Extend this mapping as the codebase evolves.
    """
    mapping = {
        "api/": "API Layer",
        "services/": "Business Services",
        "models/": "Data Models",
        "utils/": "Utility Library",
        "tests/": "Test Suite",
        "frontend/": "Frontend UI",
        "config/": "Configuration",
    }
    affected = set()
    for f in files:
        for prefix, system in mapping.items():
            if f.startswith(prefix):
                affected.add(system)
                break
    return sorted(affected)


def estimate_complexity(files: List[str]) -> Dict[str, Any]:
    """
    Simple heuristic:
      - file_count: number of files touched
      - total_lines: sum of line counts
      - size_score: file_count * avg_lines_per_file
    """
    file_count = len(files)
    total_lines = 0
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                total_lines += sum(1 for _ in fp)
        except Exception:
            continue
    avg_lines = total_lines // file_count if file_count else 0
    size_score = file_count * avg_lines
    return {
        "file_count": file_count,
        "total_lines": total_lines,
        "average_lines_per_file": avg_lines,
        "size_score": size_score,
    }


def flag_risks(affected_systems: List[str], complexity: Dict[str, Any]) -> List[str]:
    """Generate a list of risk warnings based on simple rules."""
    risks = []
    # Risk if many core systems are touched
    core_systems = {"API Layer", "Business Services", "Data Models"}
    if core_systems.intersection(set(affected_systems)):
        risks.append("Core subsystem modifications detected.")
    # High complexity score
    if complexity["size_score"] > 5000:
        risks.append("Large code impact (size_score > 5000).")
    # Few recent commits may indicate stale branch
    recent_commits = get_recent_git_commits(5)
    if not recent_commits:
        risks.append("No recent git activity detected.")
    return risks


def main() -> None:
    repo_root = Path.cwd()
    files = scan_file_tree(repo_root)

    recent_commits = get_recent_git_commits()
    affected_systems = identify_affected_systems(files)
    complexity = estimate_complexity(files)
    risks = flag_risks(affected_systems, complexity)

    summary = {
        "files_scanned": len(files),
        "recent_commits": recent_commits,
        "affected_systems": affected_systems,
        "complexity_estimate": complexity,
        "risks": risks,
    }

    # Output JSON to stdout – the caller can capture and hydrate the Expert Node.
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()