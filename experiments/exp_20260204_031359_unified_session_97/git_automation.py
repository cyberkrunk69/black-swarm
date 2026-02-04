#!/usr/bin/env python3
"""
git_automation.py

Utility to enforce an intelligent Git workflow for swarm experiments.

Features:
1. Create a feature branch for an experiment.
2. Run validation (tests, lint, etc.) before committing.
3. Produce meaningful commit messages.
4. Merge to ``main`` only when validation passes.
5. Bump project version following the project's .bumpversion.cfg conventions.

Usage example
-------------
    from git_automation import GitAutomation

    ga = GitAutomation()
    ga.create_feature_branch("exp-1234-new-algo")
    ga.run_validation()
    ga.commit_changes("feat: add new algorithm for experiment 1234")
    ga.merge_to_main()
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


class GitAutomationError(RuntimeError):
    """Custom exception for GitAutomation failures."""
    pass


class GitAutomation:
    """Encapsulates the Git workflow for swarm experiments."""

    def __init__(self, repo_root: Optional[Path] = None):
        """
        Parameters
        ----------
        repo_root : Path, optional
            Path to the repository root. If None, the directory containing this
            file's parent directories up to the first ``.git`` folder is used.
        """
        self.repo_root = repo_root or self._discover_repo_root()
        if not (self.repo_root / ".git").exists():
            raise GitAutomationError(f"'{self.repo_root}' does not appear to be a Git repo.")
        self._git = lambda *args, **kw: self._run_git(*args, cwd=self.repo_root, **kw)

    @staticmethod
    def _discover_repo_root() -> Path:
        """Walk upwards from the current file until a .git directory is found."""
        cur = Path(__file__).resolve()
        for parent in [cur] + list(cur.parents):
            if (parent / ".git").is_dir():
                return parent
        raise GitAutomationError("Unable to locate repository root (no .git directory found).")

    @staticmethod
    def _run_git(*args: str, cwd: Path, capture_output: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and raise on failure."""
        cmd = ["git"] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=capture_output,
                text=True,
                check=True,
            )
            return result
        except subprocess.CalledProcessError as exc:
            raise GitAutomationError(
                f"Git command failed: {' '.join(cmd)}\n"
                f"stdout: {exc.stdout}\nstderr: {exc.stderr}"
            ) from exc

    # --------------------------------------------------------------------- #
    # Branch handling
    # --------------------------------------------------------------------- #
    def create_feature_branch(self, branch_name: str) -> None:
        """
        Create and checkout a new feature branch based on the current ``main``.

        Parameters
        ----------
        branch_name : str
            Desired branch name (e.g., ``exp-1234-new-feature``). The method will
            prefix ``feature/`` if not already present.
        """
        if not branch_name.startswith(("feature/", "feat/")):
            branch_name = f"feature/{branch_name}"
        # Ensure we start from the latest main
        self._git("checkout", "main")
        self._git("pull", "origin", "main")
        # Create and switch to the new branch
        self._git("checkout", "-b", branch_name)
        print(f"[GitAutomation] Created and switched to branch '{branch_name}'.")

    # --------------------------------------------------------------------- #
    # Validation
    # --------------------------------------------------------------------- #
    def _default_validation_commands(self) -> List[List[str]]:
        """
        Define the validation steps to run before committing.

        Returns
        -------
        List[List[str]]
            Each inner list is a command (as a list of strings) that will be
            executed sequentially. If any command exits with a non‑zero status,
            validation fails.
        """
        # Common validation tools – adjust to your project as needed.
        return [
            ["make", "lint"],        # linting via Makefile target
            ["make", "test"],        # unit/integration tests
            ["make", "type-check"],  # optional type checking
        ]

    def run_validation(self, commands: Optional[List[List[str]]] = None) -> None:
        """
        Execute validation commands. Raises :class:`GitAutomationError` on failure.

        Parameters
        ----------
        commands : list of list of str, optional
            Custom validation commands. If omitted, the default list from
            ``_default_validation_commands`` is used.
        """
        commands = commands or self._default_validation_commands()
        for cmd in commands:
            try:
                print(f"[GitAutomation] Running validation: {' '.join(cmd)}")
                subprocess.run(
                    cmd,
                    cwd=str(self.repo_root),
                    check=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                raise GitAutomationError(
                    f"Validation step failed: {' '.join(cmd)}\n"
                    f"Return code: {exc.returncode}"
                ) from exc
        print("[GitAutomation] All validation steps passed.")

    # --------------------------------------------------------------------- #
    # Commit handling
    # --------------------------------------------------------------------- #
    def commit_changes(self, message: str, add_all: bool = True) -> None:
        """
        Stage changes (optionally all) and create a commit with a meaningful message.

        Parameters
        ----------
        message : str
            Commit message. Follow conventional commits if desired.
        add_all : bool, default True
            If True, ``git add -A`` is executed before committing.
        """
        if add_all:
            self._git("add", "-A")
        self._git("commit", "-m", message)
        print(f"[GitAutomation] Created commit with message: {message}")

    # --------------------------------------------------------------------- #
    # Version bumping (respecting .bumpversion.cfg)
    # --------------------------------------------------------------------- #
    def bump_version(self, part: str = "patch") -> None:
        """
        Bump the project version using the project's bumpversion configuration.

        Parameters
        ----------
        part : {'major', 'minor', 'patch'}
            Which part of the version to bump.
        """
        bump_cfg = self.repo_root / ".bumpversion.cfg"
        if not bump_cfg.is_file():
            raise GitAutomationError("No .bumpversion.cfg found; cannot bump version.")
        # Use bumpversion CLI if available
        try:
            self._run_git("bumpversion", part, cwd=self.repo_root, capture_output=False)
        except GitAutomationError:
            # Fallback to invoking bumpversion directly
            try:
                subprocess.run(
                    ["bumpversion", part],
                    cwd=str(self.repo_root),
                    check=True,
                )
            except Exception as exc:
                raise GitAutomationError(f"Failed to bump version: {exc}") from exc
        print(f"[GitAutomation] Version bumped ({part}).")

    # --------------------------------------------------------------------- #
    # Merge handling
    # --------------------------------------------------------------------- #
    def merge_to_main(self, branch_name: Optional[str] = None, push: bool = True) -> None:
        """
        Merge the current (or specified) branch into ``main`` after ensuring tests pass.

        Parameters
        ----------
        branch_name : str, optional
            Name of the branch to merge. If None, the currently checked‑out branch is used.
        push : bool, default True
            Whether to push the merged ``main`` back to the remote.
        """
        # Ensure validation passes on the branch we intend to merge
        self.run_validation()
        current_branch = branch_name or self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        # Switch to main, pull latest, then merge
        self._git("checkout", "main")
        self._git("pull", "origin", "main")
        self._git("merge", "--no-ff", current_branch, "-m", f"chore: merge {current_branch} into main")
        print(f"[GitAutomation] Merged '{current_branch}' into 'main'.")
        if push:
            self._git("push", "origin", "main")
            print("[GitAutomation] Pushed updated 'main' to remote.")

    # --------------------------------------------------------------------- #
    # Helper utilities
    # --------------------------------------------------------------------- #
    def get_current_branch(self) -> str:
        """Return the name of the currently checked‑out branch."""
        result = self._git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()


if __name__ == "__main__":
    # Simple CLI for quick manual usage
    import argparse

    parser = argparse.ArgumentParser(description="Automate intelligent git workflow for experiments.")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # create-feature
    p_create = subparsers.add_parser("create-feature", help="Create a new feature branch.")
    p_create.add_argument("name", help="Feature branch name (e.g., exp-1234-new-feature)")

    # commit
    p_commit = subparsers.add_parser("commit", help="Commit staged changes.")
    p_commit.add_argument("message", help="Commit message")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge current branch into main after validation.")
    p_merge.add_argument("--no-push", action="store_true", help="Do not push main after merge.")

    # bump
    p_bump = subparsers.add_parser("bump", help="Bump project version.")
    p_bump.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        default="patch",
        nargs="?",
        help="Which part of the version to bump (default: patch).",
    )

    args = parser.parse_args()
    ga = GitAutomation()

    if args.cmd == "create-feature":
        ga.create_feature_branch(args.name)
    elif args.cmd == "commit":
        ga.commit_changes(args.message)
    elif args.cmd == "merge":
        ga.merge_to_main(push=not args.no_push)
    elif args.cmd == "bump":
        ga.bump_version(args.part)
    else:
        parser.print_help()
        sys.exit(1)