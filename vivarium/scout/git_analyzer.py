"""
Git analyzer — Inspect repository state for tools like scout-commit.

Provides functions to analyze diffs, changed files, branches, and base branch
for automated tasks such as commit message generation.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def _run_git(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    """
    Run a git command. Logs the command and raises on failure.

    Raises:
        FileNotFoundError: If git executable is not found.
        subprocess.CalledProcessError: If git returns non-zero exit code.
    """
    cmd = ["git"] + args
    logger.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd,
        )
        return result
    except FileNotFoundError as e:
        logger.error("Git executable not found: %s", e)
        raise
    except subprocess.CalledProcessError as e:
        logger.warning("Git command failed: %s (stderr: %s)", " ".join(cmd), e.stderr or "")
        raise


def get_files_in_last_commit(repo_root: Optional[Path] = None) -> List[Path]:
    """
    Return files changed in the most recent commit (for post-commit hooks).

    Uses `git show --name-only --pretty=format: HEAD`.
    Returns empty list if no commits exist or on error.
    """
    try:
        result = _run_git(
            ["show", "--name-only", "--pretty=format:", "HEAD"],
            cwd=repo_root,
        )
    except subprocess.CalledProcessError:
        return []

    output = result.stdout.strip()
    if not output:
        return []

    root = Path(repo_root or ".").resolve()
    return [root / line for line in output.splitlines() if line.strip()]


def get_changed_files(
    staged_only: bool = False,
    repo_root: Optional[Path] = None,
    base_branch: Optional[str] = None,
) -> List[Path]:
    """
    Return a list of changed file paths.

    Args:
        staged_only: If True, return only staged files (--cached).
                     If False, return all working directory changes vs HEAD.
        repo_root: Optional working directory for the git command. Defaults to cwd.
        base_branch: If set, return files changed in current branch vs base
                     (e.g. "origin/main"). Uses `git diff --name-only base...HEAD`.

    Returns:
        List of pathlib.Path objects representing changed files.
    """
    try:
        if base_branch:
            result = _run_git(
                ["diff", "--name-only", f"{base_branch}...HEAD"],
                cwd=repo_root,
            )
        elif staged_only:
            result = _run_git(["diff", "--name-only", "--cached"], cwd=repo_root)
        else:
            result = _run_git(["diff", "--name-only", "HEAD"], cwd=repo_root)
    except subprocess.CalledProcessError:
        return []

    output = result.stdout.strip()
    if not output:
        return []

    root = Path(repo_root or ".").resolve()
    return [root / line for line in output.splitlines() if line.strip()]


def get_diff_for_file(
    file_path: Path,
    staged_only: bool = False,
    repo_root: Optional[Path] = None,
) -> str:
    """
    Return the raw diff string for the specified file.

    Args:
        file_path: Path to the file (relative to repo root or absolute).
        staged_only: If True, diff staged changes (--cached).
                     If False, diff working directory vs HEAD.
        repo_root: Optional working directory for the git command. Defaults to cwd.

    Returns:
        Raw diff string, or empty string on error.
    """
    path_str = str(file_path)
    try:
        if staged_only:
            result = _run_git(["diff", "--cached", path_str], cwd=repo_root)
        else:
            result = _run_git(["diff", "HEAD", path_str], cwd=repo_root)
    except subprocess.CalledProcessError:
        return ""

    return result.stdout or ""


def get_current_branch(repo_root: Optional[Path] = None) -> str:
    """
    Return the name of the current branch.

    Args:
        repo_root: Optional working directory for the git command. Defaults to cwd.

    Returns:
        Branch name, or empty string if not on a branch (detached HEAD) or on error.
    """
    try:
        result = _run_git(["branch", "--show-current"], cwd=repo_root)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def has_remote_origin(repo_root: Optional[Path] = None) -> bool:
    """Return True if remote 'origin' is configured."""
    try:
        _run_git(["remote", "get-url", "origin"], cwd=repo_root)
        return True
    except subprocess.CalledProcessError:
        return False


def is_remote_empty(repo_root: Optional[Path] = None) -> bool:
    """
    Return True if origin has no branches (e.g., fresh repo).

    Runs `git ls-remote --heads origin`. Returns False on error (network, etc).
    """
    try:
        result = _run_git(["ls-remote", "--heads", "origin"], cwd=repo_root)
        return not result.stdout.strip()
    except subprocess.CalledProcessError:
        return False


def get_default_base_ref(repo_root: Optional[Path] = None) -> Optional[str]:
    """
    Return origin/main or origin/master if either exists as a ref.

    Tries origin/main first, then origin/master. Returns None if both fail.
    """
    for ref in ("origin/main", "origin/master"):
        try:
            _run_git(["rev-parse", ref], cwd=repo_root)
            return ref
        except subprocess.CalledProcessError:
            continue
    return None


def get_git_version(repo_root: Optional[Path] = None) -> str:
    """
    Return version from git describe --tags, or v0.1.0-dev if no tags.
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True,
            text=True,
            cwd=repo_root or Path.cwd(),
            check=False,
        )
        out = (result.stdout or "").strip()
        if out and not out.startswith("v"):
            return f"v{out}"
        return out or "v0.1.0-dev"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "v0.1.0-dev"


def get_git_commit_hash(repo_root: Optional[Path] = None) -> str:
    """Return current commit hash (short)."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=repo_root or Path.cwd(),
            check=False,
        )
        return (result.stdout or "").strip() or "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def get_upstream_ref(repo_root: Optional[Path] = None) -> Optional[str]:
    """
    Return the upstream tracking ref for the current branch, if set.

    Uses `git rev-parse --abbrev-ref --symbolic-full-name @{u}`.
    Returns e.g. "origin/main" or None if not on a branch or no upstream.
    """
    try:
        result = _run_git(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            cwd=repo_root,
        )
        ref = result.stdout.strip()
        return ref if ref else None
    except subprocess.CalledProcessError:
        return None


def get_base_branch(
    current_branch: str,
    repo_root: Optional[Path] = None,
) -> Optional[str]:
    """
    Attempt to determine the base branch for the current branch.

    Tries, in order:
    1. Remote tracking branch upstream (e.g., origin/main)
    2. Existence of 'main'
    3. Existence of 'master'
    4. Existence of 'develop'

    Args:
        current_branch: Name of the current branch.
        repo_root: Optional working directory for the git command. Defaults to cwd.

    Returns:
        Base branch name (e.g., "main") or None if ambiguous/unavailable.
    """
    if not current_branch:
        return None

    try:
        # 1. Try remote tracking branch: git rev-parse --abbrev-ref --symbolic-full-name @{u}
        result = _run_git(
            ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
            cwd=repo_root,
        )
        upstream = result.stdout.strip()
        if upstream:
            # upstream is e.g. "origin/main" or "origin/master"
            if "/" in upstream:
                base = upstream.split("/", 1)[1]
                # Only use if it's a different branch (e.g. main, not feature/foo)
                if base != current_branch:
                    logger.debug("Base branch from upstream: %s", base)
                    return base
    except subprocess.CalledProcessError:
        pass

    # 2. Fall back to common conventions: check if main, master, develop exist
    for candidate in ("main", "master", "develop"):
        try:
            _run_git(["rev-parse", "--verify", candidate], cwd=repo_root)
            logger.debug("Base branch from convention: %s", candidate)
            return candidate
        except subprocess.CalledProcessError:
            continue

    logger.debug("Could not determine base branch for %s", current_branch)
    return None
