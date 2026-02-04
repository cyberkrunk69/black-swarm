#!/usr/bin/env python3
"""
gut_check_planner.py

Quick initial analysis tool for the unified session experiment.
It:
  * Scans the repository file tree (Python source files).
  * Reads recent Git history to find recently touched files.
  * Identifies "affected systems" based on import heuristics.
  * Estimates code complexity (lines, functions, classes).
  * Flags potential risk indicators.
  * Emits a JSON summary that can be used to HYDRATE the Expert Node.
"""

import os
import json
import subprocess
import ast
from collections import defaultdict
from typing import List, Dict, Any

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
# Number of recent commits to consider when gathering changed files.
RECENT_COMMITS = 10

# Maximum lines of code in a single file before flagging a size risk.
MAX_LINES_PER_FILE = 800

# Maximum number of functions/classes before flagging a complexity risk.
MAX_FUNCS_PER_FILE = 30
MAX_CLASSES_PER_FILE = 20

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def run_git_command(args: List[str]) -> str:
    """Run a git command and return its stdout as a string."""
    result = subprocess.run(
        ["git"] + args,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def get_recently_changed_files(n: int = RECENT_COMMITS) -> List[str]:
    """Return a list of files touched in the last `n` commits."""
    log_output = run_git_command(
        ["log", f"-n{n}", "--pretty=format:", "--name-only"]
    )
    files = {line for line in log_output.splitlines() if line}
    # Filter to repository root files only
    return sorted(files)


def parse_python_file(path: str) -> ast.Module:
    """Parse a Python file into an AST, returning an empty module on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        return ast.parse(source, filename=path)
    except Exception:
        return ast.Module(body=[])


def analyze_complexity(tree: ast.Module) -> Dict[str, int]:
    """Count functions and classes in an AST."""
    funcs = sum(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    classes = sum(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
    return {"functions": funcs, "classes": classes}


def extract_imports(tree: ast.Module) -> List[str]:
    """Return a list of top‑level imported module names."""
    imports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def scan_repository(root: str = ".") -> List[Dict[str, Any]]:
    """Walk the repo and collect analysis data for each Python file."""
    analysis = []
    for dirpath, _, filenames in os.walk(root):
        # Skip hidden directories and virtual envs
        if any(part.startswith(".") for part in dirpath.split(os.sep)):
            continue
        if "venv" in dirpath or "env" in dirpath:
            continue

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root)

            # Basic file metrics
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                line_count = len(lines)
            except Exception:
                line_count = 0
                lines = []

            tree = parse_python_file(full_path)
            comp = analyze_complexity(tree)
            imports = extract_imports(tree)

            analysis.append(
                {
                    "path": rel_path,
                    "lines": line_count,
                    "functions": comp["functions"],
                    "classes": comp["classes"],
                    "imports": imports,
                }
            )
    return analysis


def identify_affected_systems(file_analysis: List[Dict[str, Any]]) -> List[str]:
    """
    Very simple heuristic: treat top‑level imports that match a known
    internal subsystem prefix as an "affected system".
    """
    # Example mapping – extend as needed for your project.
    subsystem_prefixes = ["core", "api", "services", "models", "utils"]
    affected = set()
    for entry in file_analysis:
        for imp in entry["imports"]:
            for prefix in subsystem_prefixes:
                if imp.startswith(prefix):
                    affected.add(prefix)
    return sorted(affected)


def estimate_complexity(file_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate simple complexity metrics across the repo."""
    total_files = len(file_analysis)
    total_lines = sum(f["lines"] for f in file_analysis)
    total_funcs = sum(f["functions"] for f in file_analysis)
    total_classes = sum(f["classes"] for f in file_analysis)

    avg_lines = total_lines / total_files if total_files else 0
    avg_funcs = total_funcs / total_files if total_files else 0
    avg_classes = total_classes / total_files if total_files else 0

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "total_functions": total_funcs,
        "total_classes": total_classes,
        "average_lines_per_file": round(avg_lines, 1),
        "average_functions_per_file": round(avg_funcs, 1),
        "average_classes_per_file": round(avg_classes, 1),
    }


def flag_risks(file_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create a list of risk flags based on size and complexity thresholds."""
    risks = []
    for f in file_analysis:
        if f["lines"] > MAX_LINES_PER_FILE:
            risks.append(
                {
                    "path": f["path"],
                    "type": "size",
                    "detail": f"File has {f['lines']} lines (> {MAX_LINES_PER_FILE})",
                }
            )
        if f["functions"] > MAX_FUNCS_PER_FILE:
            risks.append(
                {
                    "path": f["path"],
                    "type": "function_complexity",
                    "detail": f"{f['functions']} functions (> {MAX_FUNCS_PER_FILE})",
                }
            )
        if f["classes"] > MAX_CLASSES_PER_FILE:
            risks.append(
                {
                    "path": f["path"],
                    "type": "class_complexity",
                    "detail": f"{f['classes']} classes (> {MAX_CLASSES_PER_FILE})",
                }
            )
    return risks


def build_context_summary() -> Dict[str, Any]:
    """Collect everything into the JSON structure expected by the Expert Node."""
    repo_root = os.getcwd()
    file_data = scan_repository(repo_root)
    recent_files = get_recently_changed_files()
    affected_systems = identify_affected_systems(file_data)
    complexity = estimate_complexity(file_data)
    risks = flag_risks(file_data)

    summary = {
        "experiment": "exp_20260204_031203_unified_session_38",
        "generated_at": subprocess.check_output(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]
        ).decode().strip(),
        "file_analysis": file_data,
        "recently_changed_files": recent_files,
        "identified_systems": affected_systems,
        "complexity_estimate": complexity,
        "risk_flags": risks,
    }
    return summary


def main() -> None:
    """Entry point – print the JSON summary to stdout."""
    summary = build_context_summary()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()