#!/usr/bin/env python3
"""
git_automation.py

Utility for the Swarm to handle a disciplined Git workflow:

1. Create a feature branch for an experiment.
2. Run validation (tests, lint, static analysis) before any commit.
3. Enforce meaningful commit messages.
4. Merge back to ``main`` only when the full test suite passes.
5. Keep versioning in sync with the project's ``.bumpversion.cfg`` and ``Makefile``.

The script is deliberately lightweight – it relies only on the standard library
and the project's existing ``make`` targets.  It can be invoked from the
command line or imported as a module.

Typical usage:

    $ python git_automation.py start my_experiment
    $ python git_automation.py commit -m "Add novel data loader"
    $ python git_automation.py merge

"""

from __future__ import annotations

import argparse
import configparser
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #


def _run_cmd(cmd: List[str], capture_output: bool = False, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command, raising on failure."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.PIPE if capture_output else None,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        if capture_output:
            print("STDOUT:", result.stdout, file=sys.stderr)
            print("STDERR:", result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return result


def _git_current_branch() -> str:
    result = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True)
    return result.stdout.strip()


def _git_branch_exists(branch: str) -> bool:
    result = _run_cmd(["git", "branch", "--list", branch], capture_output=True, check=False)
    return bool(result.stdout.strip())


def _load_bumpversion_cfg() -> configparser.ConfigParser:
    cfg_path = Path(".bumpversion.cfg")
    if not cfg_path.is_file():
        print("⚠️  .bumpversion.cfg not found – version bumping will be skipped.", file=sys.stderr)
        return configparser.ConfigParser()
    cfg = configparser.ConfigParser()
    cfg.read(cfg_path)
    return cfg


def _current_version() -> str | None:
    cfg = _load_bumpversion_cfg()
    if "bumpversion" in cfg and "current_version" in cfg["bumpversion"]:
        return cfg["bumpversion"]["current_version"]
    return None


def _bump_version(part: str = "patch") -> None:
    """
    Use bumpversion (if installed) to bump the version according to the
    project's .bumpversion.cfg.  The function is defensive – if the tool
    is missing it simply prints a warning.
    """
    if not shutil.which("bumpversion"):
        print("⚠️  bumpversion not installed – skipping version bump.", file=sys.stderr)
        return
    _run_cmd(["bumpversion", part])


def _run_validation() -> bool:
    """
    Execute the project's test suite via ``make test`` (or ``make all`` if
    ``test`` is not defined). Returns True if the suite passes.
    """
    # Prefer explicit ``make test``; fallback to ``make all``.
    make_targets = ["test", "all"]
    for target in make_targets:
        result = _run_cmd(["make", target], capture_output=True, check=False)
        if result.returncode == 0:
            return True
        # If the target does not exist, ``make`` returns 2 – try next.
        if result.returncode == 2:
            continue
        # Any other non‑zero exit means failure.
        print(f"Validation failed on target '{target}'.", file=sys.stderr)
        return False
    print("No recognizable test target found in Makefile.", file=sys.stderr)
    return False


def _ensure_clean_worktree() -> None:
    """Abort if there are uncommitted changes."""
    result = _run_cmd(["git", "status", "--porcelain"], capture_output=True)
    if result.stdout.strip():
        print("❌ Working tree is dirty. Please commit or stash changes before proceeding.", file=sys.stderr)
        sys.exit(1)


# --------------------------------------------------------------------------- #
# Core workflow commands
# --------------------------------------------------------------------------- #


def start_branch(exp_name: str) -> None:
    """
    Create and checkout a new feature branch named ``exp/<exp_name>``.
    The branch is based on the current ``main`` (or ``master``) tip.
    """
    base_branch = "main" if _git_branch_exists("main") else "master"
    _run_cmd(["git", "checkout", base_branch])
    _run_cmd(["git", "pull", "--ff-only"])

    branch_name = f"exp/{exp_name}"
    if _git_branch_exists(branch_name):
        print(f"⚠️  Branch '{branch_name}' already exists – checking it out.", file=sys.stderr)
        _run_cmd(["git", "checkout", branch_name])
    else:
        _run_cmd(["git", "checkout", "-b", branch_name])
    print(f"✅ Created and switched to branch '{branch_name}'.")


def commit_changes(message: str) -> None:
    """
    Validate, stage all changes, and commit with the supplied message.
    The message must be at least 10 characters and contain a verb.
    """
    _ensure_clean_worktree()  # ensure we start from a clean state

    if len(message.strip()) < 10:
        print("❌ Commit message too short – please provide a more descriptive message.", file=sys.stderr)
        sys.exit(1)

    # Simple heuristic for a "meaningful" message: must contain a verb.
    if not re.search(r"\b(add|remove|fix|update|refactor|implement|change|create|deprecate)\b", message, re.IGNORECASE):
        print("❌ Commit message should contain an action verb (add, fix, update, etc.).", file=sys.stderr)
        sys.exit(1)

    # Run validation before committing.
    if not _run_validation():
        print("❌ Validation failed – aborting commit.", file=sys.stderr)
        sys.exit(1)

    # Stage everything (feel free to adjust to a more granular pattern).
    _run_cmd(["git", "add", "-A"])

    # Commit.
    _run_cmd(["git", "commit", "-m", message])
    print("✅ Commit created.")


def merge_to_main() -> None:
    """
    Merge the current feature branch back into ``main`` (or ``master``) after
    a successful validation run.  The merge is performed via a fast‑forward
    or a no‑ff merge, depending on the project's policy (here we use --no-ff
    to retain history).
    """
    current_branch = _git_current_branch()
    if not current_branch.startswith("exp/"):
        print("❌ You must be on an experiment branch (exp/...) to merge.", file=sys.stderr)
        sys.exit(1)

    # Ensure the branch is up‑to‑date with its base.
    base_branch = "main" if _git_branch_exists("main") else "master"
    _run_cmd(["git", "checkout", base_branch])
    _run_cmd(["git", "pull", "--ff-only"])

    # Run validation on the target branch before merging.
    print("🔎 Running validation on target branch before merge...")
    if not _run_validation():
        print("❌ Validation on target branch failed – aborting merge.", file=sys.stderr)
        sys.exit(1)

    # Merge the experiment branch.
    _run_cmd(["git", "merge", "--no-ff", current_branch])
    print(f"✅ Merged '{current_branch}' into '{base_branch}'.")

    # Optional: bump version automatically after a successful merge.
    # Many projects bump the patch version on every release.
    try:
        import shutil
        if shutil.which("bumpversion"):
            _bump_version("patch")
            _run_cmd(["git", "push"])
    except Exception:
        pass

    # Push the updated main branch.
    _run_cmd(["git", "push"])


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automated Git workflow for Swarm experiments.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start = subparsers.add_parser("start", help="Create a new experiment branch.")
    start.add_argument("name", help="Name of the experiment (will become exp/<name>).")

    # commit
    commit = subparsers.add_parser("commit", help="Validate and commit changes.")
    commit.add_argument("-m", "--message", required=True, help="Commit message (must be meaningful).")

    # merge
    subparsers.add_parser("merge", help="Merge current experiment branch into main after tests pass.")

    return parser


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "start":
        start_branch(args.name)
    elif args.command == "commit":
        commit_changes(args.message)
    elif args.command == "merge":
        merge_to_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()