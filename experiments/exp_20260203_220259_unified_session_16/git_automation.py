#!/usr/bin/env python3
"""
git_automation.py

Utility to enforce a lightweight, opinionated Git workflow for the
swarm‑based experimentation repository.

Features
--------
1. Create a feature branch for a given experiment name.
2. Run project validation (Makefile target `test` by default) before
   committing any changes.
3. Commit with a structured, meaningful message.
4. Merge back to `main` only when validation succeeds.
5. Bump the project version using the conventions defined in
   `.bumpversion.cfg` (optional).

Usage
-----
    python git_automation.py create-branch <exp_name>
    python git_automation.py commit -m "Your commit message"
    python git_automation.py merge-to-main
    python git_automation.py bump-version [patch|minor|major]

The script assumes it is executed from the repository root.
"""

import argparse
import subprocess
import sys
import os
import configparser
from pathlib import Path

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def run_cmd(cmd, capture_output=False, check=True):
    """Run a shell command, optionally capturing its output."""
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE if capture_output else None,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check and result.returncode != 0:
        print(f"Command failed [{cmd}]:")
        if capture_output:
            print(result.stdout)
        sys.exit(result.returncode)
    return result.stdout.strip() if capture_output else None


def git_current_branch():
    return run_cmd("git rev-parse --abbrev-ref HEAD", capture_output=True)


def ensure_clean_worktree():
    status = run_cmd("git status --porcelain", capture_output=True)
    if status:
        print("Working tree is not clean. Please commit or stash changes first.")
        sys.exit(1)


def validate_project():
    """Run validation as defined in the Makefile (default target `test`)."""
    print("Running project validation (make test)...")
    run_cmd("make test")
    print("✅ Validation passed.")


def read_version():
    """Read the current version from .bumpversion.cfg."""
    cfg_path = Path(".bumpversion.cfg")
    if not cfg_path.is_file():
        return None
    parser = configparser.ConfigParser()
    parser.read(cfg_path)
    try:
        return parser["bumpversion"]["current_version"]
    except KeyError:
        return None


def bump_version(part: str):
    """Bump version using bump2version (must be installed)."""
    if part not in {"major", "minor", "patch"}:
        print(f"Invalid bump part: {part}. Choose from major/minor/patch.")
        sys.exit(1)
    print(f"Bumping {part} version...")
    run_cmd(f"bump2version {part}")
    new_version = read_version()
    print(f"🚀 New version: {new_version}")


# --------------------------------------------------------------------------- #
# Core workflow commands
# --------------------------------------------------------------------------- #

def create_branch(exp_name: str):
    """Create a new feature branch for the given experiment."""
    ensure_clean_worktree()
    branch_name = f"exp/{exp_name}"
    print(f"Creating branch '{branch_name}' from 'main'...")
    run_cmd("git fetch origin")
    run_cmd("git checkout main")
    run_cmd("git pull origin main")
    run_cmd(f"git checkout -b {branch_name}")
    print(f"✅ Branch '{branch_name}' created and checked out.")


def commit_changes(message: str):
    """Stage all changes, run validation, then commit."""
    ensure_clean_worktree()
    print("Staging all changes...")
    run_cmd("git add -A")
    # Run validation before committing
    validate_project()
    print(f"Committing with message: {message}")
    run_cmd(f'git commit -m "{message}"')
    print("✅ Commit created.")


def merge_to_main():
    """Merge the current feature branch back to main after validation."""
    current = git_current_branch()
    if current == "main":
        print("You are already on 'main'. Nothing to merge.")
        sys.exit(0)

    # Ensure branch is up‑to‑date with remote
    print(f"Fetching latest 'main' from origin...")
    run_cmd("git fetch origin")
    run_cmd("git checkout main")
    run_cmd("git pull origin main")

    # Validate on the feature branch before merging
    print(f"Switching back to feature branch '{current}' for validation...")
    run_cmd(f"git checkout {current}")
    validate_project()

    # Merge
    print(f"Merging '{current}' into 'main'...")
    run_cmd(f"git checkout main")
    run_cmd(f"git merge --no-ff {current}")

    # Push result
    print("Pushing merged 'main' to remote...")
    run_cmd("git push origin main")
    print("✅ Merge completed and pushed.")


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #

def build_parser():
    parser = argparse.ArgumentParser(
        description="Automate the git workflow for experiments."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-branch
    cp = subparsers.add_parser(
        "create-branch", help="Create a feature branch for an experiment."
    )
    cp.add_argument("exp_name", help="Experiment identifier (e.g., 20260203_220259)")

    # commit
    cm = subparsers.add_parser(
        "commit", help="Stage, validate, and commit changes."
    )
    cm.add_argument("-m", "--message", required=True, help="Commit message")

    # merge-to-main
    subparsers.add_parser(
        "merge-to-main", help="Validate and merge current branch into main."
    )

    # bump-version
    bv = subparsers.add_parser(
        "bump-version", help="Bump project version using bump2version."
    )
    bv.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        help="Which part of the version to bump.",
    )

    return parser


def main():
    # Ensure we are running from repository root (presence of .git)
    if not Path(".git").exists():
        print("Error: .git directory not found. Run this script from the repo root.")
        sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create-branch":
        create_branch(args.exp_name)
    elif args.command == "commit":
        commit_changes(args.message)
    elif args.command == "merge-to-main":
        merge_to_main()
    elif args.command == "bump-version":
        bump_version(args.part)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()