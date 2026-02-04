#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the repository.

Features:
- Scans the repository file tree.
- Reads recent git history (default last 30 commits).
- Identifies "affected systems" based on path heuristics.
- Estimates change complexity.
- Flags potential risks.
- Emits a JSON summary suitable for hydrating an Expert Node.
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from collections import Counter, defaultdict

# ----------------------------------------------------------------------
# Configuration (tunable via CLI)
# ----------------------------------------------------------------------
DEFAULT_COMMITS = 30
RISK_LINE_THRESHOLD = 200   # lines changed that trigger a risk flag
RISK_FILE_COUNT = 20        # number of files changed that trigger a risk flag
CORE_DIRS = {"core", "engine", "grind_spawner", "safety"}  # directories considered critical


def run_git_log(num_commits: int) -> list:
    """Return a list of commit hashes for the most recent `num_commits`."""
    try:
        result = subprocess.run(
            ["git", "rev-list", f"-n{num_commits}", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error obtaining git history: {e}")
        return []


def git_diff_stats(commits: list) -> dict:
    """
    Gather diff stats for the supplied commit list.
    Returns a dict:
        {
            "files": {filepath: {"added": int, "deleted": int, "changed": int}},
            "total_added": int,
            "total_deleted": int,
            "total_changed": int,
        }
    """
    stats = defaultdict(lambda: {"added": 0, "deleted": 0, "changed": 0})
    total_added = total_deleted = total_changed = 0

    for commit in commits:
        try:
            diff = subprocess.run(
                ["git", "show", "--numstat", "--format=", commit],
                capture_output=True,
                text=True,
                check=True,
            )
            for line in diff.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) != 3:
                    continue  # skip binary files or unexpected lines
                added, deleted, path = parts
                added = int(added) if added.isdigit() else 0
                deleted = int(deleted) if deleted.isdigit() else 0
                changed = added + deleted

                stats[path]["added"] += added
                stats[path]["deleted"] += deleted
                stats[path]["changed"] += changed

                total_added += added
                total_deleted += deleted
                total_changed += changed
        except subprocess.CalledProcessError:
            continue

    return {
        "files": dict(stats),
        "total_added": total_added,
        "total_deleted": total_deleted,
        "total_changed": total_changed,
    }


def scan_file_tree(root: Path) -> list:
    """Return a list of all files (relative to repo root) under `root`."""
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(root)))
    return files


def identify_affected_systems(changed_files: list) -> dict:
    """
    Heuristic mapping of changed files to high‑level system groups.
    Returns a dict: {system_name: [file1, file2, ...]}
    """
    system_map = defaultdict(list)
    for f in changed_files:
        parts = Path(f).parts
        # Find first part that matches a known system directory
        matched = None
        for part in parts:
            if part.lower() in CORE_DIRS:
                matched = part.lower()
                break
        if matched:
            system_map[matched].append(f)
        else:
            system_map["misc"].append(f)
    return dict(system_map)


def estimate_complexity(stats: dict) -> dict:
    """
    Very simple complexity estimation based on number of files and lines changed.
    Returns a dict with a qualitative rating.
    """
    file_count = len(stats["files"])
    line_changes = stats["total_changed"]

    # Simple scoring
    score = file_count * 0.5 + line_changes * 0.01

    if score < 5:
        level = "trivial"
    elif score < 20:
        level = "moderate"
    elif score < 50:
        level = "complex"
    else:
        level = "highly_complex"

    return {
        "file_count": file_count,
        "line_changes": line_changes,
        "score": round(score, 2),
        "complexity_level": level,
    }


def flag_risks(complexity: dict, stats: dict, affected_systems: dict) -> list:
    """Return a list of risk strings."""
    risks = []

    if complexity["line_changes"] > RISK_LINE_THRESHOLD:
        risks.append(
            f"Large line change volume ({complexity['line_changes']} lines)."
        )
    if complexity["file_count"] > RISK_FILE_COUNT:
        risks.append(
            f"Many files changed ({complexity['file_count']} files)."
        )
    # Core system modifications
    core_modified = [s for s in affected_systems if s in CORE_DIRS]
    if core_modified:
        risks.append(
            f"Core systems touched: {', '.join(sorted(core_modified))}."
        )
    # Any deletions?
    deletions = sum(
        1 for f, d in stats["files"].items() if d["deleted"] > 0 and d["added"] == 0
    )
    if deletions:
        risks.append(f"{deletions} file(s) appear to be deletions.")

    return risks


def build_summary(
    repo_root: Path,
    commits: list,
    stats: dict,
    affected_systems: dict,
    complexity: dict,
    risks: list,
) -> dict:
    """Compose the final JSON payload."""
    return {
        "repo_root": str(repo_root),
        "analyzed_commits": commits,
        "file_stats": {
            "total_files_changed": len(stats["files"]),
            "total_lines_added": stats["total_added"],
            "total_lines_deleted": stats["total_deleted"],
            "total_lines_changed": stats["total_changed"],
        },
        "affected_systems": affected_systems,
        "complexity": complexity,
        "risks": risks,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Quick gut‑check planner for the repository."
    )
    parser.add_argument(
        "--commits",
        type=int,
        default=DEFAULT_COMMITS,
        help="Number of recent commits to analyse (default: %(default)s)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write JSON summary to a file instead of stdout.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()

    # 1. Gather recent commits
    commits = run_git_log(args.commits)

    # 2. Compute diff stats across those commits
    stats = git_diff_stats(commits)

    # 3. Identify affected systems
    affected_systems = identify_affected_systems(list(stats["files"].keys()))

    # 4. Estimate complexity
    complexity = estimate_complexity(stats)

    # 5. Flag risks
    risks = flag_risks(complexity, stats, affected_systems)

    # 6. Build summary
    summary = build_summary(
        repo_root,
        commits,
        stats,
        affected_systems,
        complexity,
        risks,
    )

    json_output = json.dumps(summary, indent=2)

    if args.output:
        args.output.write_text(json_output, encoding="utf-8")
    else:
        print(json_output)


if __name__ == "__main__":
    main()