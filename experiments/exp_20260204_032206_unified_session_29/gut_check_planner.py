#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool.
- Scans the repository file tree.
- Extracts recent git history.
- Identifies high‑level affected systems (heuristic based on paths).
- Estimates overall complexity (lines of code, file count).
- Flags potential risks (large changes, TODO/FIXME markers, etc.).

Outputs a JSON structure suitable for hydrating an Expert Node.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any


def scan_file_tree(root: Path) -> List[Dict[str, Any]]:
    """Recursively walk the directory tree and collect file metadata."""
    files = []
    for path in root.rglob("*"):
        if path.is_file():
            try:
                size = path.stat().st_size
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
                files.append(
                    {
                        "relative_path": str(path.relative_to(root)),
                        "size_bytes": size,
                        "line_count": len(lines),
                    }
                )
            except Exception:
                # Skip unreadable files
                continue
    return files


def get_git_history(root: Path, max_commits: int = 20) -> List[Dict[str, Any]]:
    """Return a list of recent commits (hash, author, date, message)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", f"-n{max_commits}", "--pretty=format:%H%x1f%an%x1f%ad%x1f%s"],
            capture_output=True,
            text=True,
            check=True,
        )
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            sha, author, date, message = line.split("\x1f")
            commits.append(
                {
                    "sha": sha,
                    "author": author,
                    "date": date,
                    "message": message,
                }
            )
        return commits
    except subprocess.CalledProcessError:
        return []


def identify_affected_systems(files: List[Dict[str, Any]]) -> List[str]:
    """Heuristic mapping of file paths to high‑level system domains."""
    system_keywords = {
        "api": "API",
        "db": "Database",
        "models": "Data Model",
        "views": "Presentation",
        "controllers": "Control Layer",
        "services": "Business Logic",
        "utils": "Utilities",
        "tests": "Testing",
        "infra": "Infrastructure",
        "auth": "Authentication",
        "payment": "Payments",
        "scheduler": "Scheduling",
    }

    detected = set()
    for f in files:
        parts = f["relative_path"].lower().split(os.sep)
        for keyword, system in system_keywords.items():
            if keyword in parts:
                detected.add(system)
    return sorted(detected)


def estimate_complexity(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Very rough complexity estimate based on size and count."""
    total_files = len(files)
    total_lines = sum(f["line_count"] for f in files)
    total_bytes = sum(f["size_bytes"] for f in files)

    # Simple tiered scoring
    complexity_score = (
        (total_files // 50)
        + (total_lines // 2000)
        + (total_bytes // (100 * 1024))
    )
    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_bytes": total_bytes,
        "complexity_score": complexity_score,
    }


def flag_risks(files: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> List[str]:
    """Detect risk signals."""
    risks = []

    # Large change risk
    if len(commits) > 0 and len(commits) < 5 and len(files) > 100:
        risks.append("Large number of files changed in few commits")

    # TODO/FIXME markers
    todo_count = 0
    for f in files:
        path = Path(f["relative_path"])
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            if "TODO" in content or "FIXME" in content:
                todo_count += 1
        except Exception:
            continue
    if todo_count:
        risks.append(f"{todo_count} files contain TODO/FIXME markers")

    # High complexity
    complexity = estimate_complexity(files)
    if complexity["complexity_score"] > 10:
        risks.append("High estimated complexity")

    return risks


def build_context_summary(root_dir: str = ".") -> Dict[str, Any]:
    root = Path(root_dir).resolve()
    file_tree = scan_file_tree(root)
    git_history = get_git_history(root)
    affected_systems = identify_affected_systems(file_tree)
    complexity = estimate_complexity(file_tree)
    risk_flags = flag_risks(file_tree, git_history)

    return {
        "file_tree": file_tree,
        "git_history": git_history,
        "affected_systems": affected_systems,
        "complexity_estimate": complexity,
        "risk_flags": risk_flags,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Quick gut‑check analysis for the repo.")
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory of the repository (default: current directory).",
    )
    args = parser.parse_args()

    summary = build_context_summary(args.root)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()