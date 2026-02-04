"""
experiment_promotion.py

Utility for automatically promoting a passed experiment into the main codebase.

Usage:
    from app.experiment_promotion import promote_experiment
    promote_experiment("<path-to-experiment-directory>")
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from git import Repo, Actor

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _load_result_json(experiment_dir: Path) -> Dict[str, Any]:
    """Load the result.json produced by an experiment."""
    result_path = experiment_dir / "result.json"
    if not result_path.is_file():
        raise FileNotFoundError(f"Result file not found: {result_path}")
    with result_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _apply_diff(repo: Repo, diff_text: str) -> None:
    """
    Apply a unified diff to the repository using `git apply`.

    Raises RuntimeError if the diff cannot be cleanly applied.
    """
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
        tmp.write(diff_text)
        tmp_path = Path(tmp.name)

    try:
        # First, ensure the diff can be applied cleanly.
        repo.git.apply("--check", str(tmp_path))
        # Apply the diff.
        repo.git.apply(str(tmp_path))
    except Exception as e:
        raise RuntimeError(f"Failed to apply diff: {e}") from e
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def _stage_and_commit(
    repo: Repo,
    files: List[Path],
    author_name: str,
    author_email: str,
    message: str,
) -> None:
    """Stage the given files and create a commit with the supplied author."""
    repo.index.add([str(f) for f in files])
    author = Actor(author_name, author_email)
    repo.index.commit(message, author=author, committer=author)


def _bump_version_if_needed(repo_root: Path, diffs: List[Dict[str, Any]]) -> None:
    """
    If any diff is marked as significant, bump the package version in pyproject.toml.
    Simple bump: increment the patch number (e.g., 1.2.3 -> 1.2.4).
    """
    if not any(d.get("significant", False) for d in diffs):
        return

    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.is_file():
        # Fallback to setup.py if pyproject.toml is absent.
        pyproject_path = repo_root / "setup.py"
        if not pyproject_path.is_file():
            return  # No version file to bump.

    # Read the file.
    content = pyproject_path.read_text(encoding="utf-8")
    import re

    version_pattern = re.compile(r'(?P<prefix>version\s*=\s*["\'])(?P<ver>\d+\.\d+\.\d+)(?P<suffix>["\'])')
    match = version_pattern.search(content)
    if not match:
        # Try a generic __version__ pattern.
        version_pattern = re.compile(r'(?P<prefix>__version__\s*=\s*["\'])(?P<ver>\d+\.\d+\.\d+)(?P<suffix>["\'])')
        match = version_pattern.search(content)

    if not match:
        raise RuntimeError("Unable to locate version string to bump.")

    major, minor, patch = map(int, match.group("ver").split("."))
    new_version = f"{major}.{minor}.{patch + 1}"
    new_content = (
        content[: match.start("ver")] + new_version + content[match.end("ver") :]
    )
    pyproject_path.write_text(new_content, encoding="utf-8")

    # Commit the version bump.
    repo = Repo(str(repo_root))
    repo.index.add([str(pyproject_path)])
    author = Actor("experiment-promotion-bot", "bot@example.com")
    repo.index.commit(
        f"Bump version to {new_version} (auto‑generated after experiment promotion)",
        author=author,
        committer=author,
    )


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def promote_experiment(experiment_dir: str) -> None:
    """
    Promote a passed experiment into the main codebase.

    Parameters
    ----------
    experiment_dir : str
        Path to the directory containing the experiment's artifacts,
        notably a ``result.json`` file with the following schema:

        {
            "status": "passed" | "failed",
            "author": {"name": "...", "email": "..."},
            "description": "Short description of the experiment",
            "changes": [
                {
                    "file_path": "relative/path/to/file.py",
                    "diff": "<unified diff>",
                    "significant": true|false   # optional, defaults to false
                },
                ...
            ]
        }

    The function will:
        * Verify the status is ``passed``.
        * Apply each diff in order, aborting on the first conflict.
        * Create a git commit with the experiment author's attribution.
        * Optionally bump the package version if any change is marked significant.
    """
    repo_root = Path(__file__).resolve().parent.parent  # assuming /app is repo root
    repo = Repo(str(repo_root))

    experiment_path = Path(experiment_dir).resolve()
    result = _load_result_json(experiment_path)

    if result.get("status") != "passed":
        raise RuntimeError(f"Experiment {experiment_path} did not pass all tests.")

    author_info = result.get("author", {})
    author_name = author_info.get("name", "unknown")
    author_email = author_info.get("email", "unknown@example.com")
    description = result.get("description", "Experiment promotion")

    changes = result.get("changes", [])
    if not changes:
        raise RuntimeError("No changes found in experiment result.")

    # Track which files we modify for staging later.
    modified_files: List[Path] = []

    # Apply diffs sequentially, detecting conflicts.
    for change in changes:
        rel_path = change["file_path"]
        diff_text = change["diff"]
        target_path = repo_root / rel_path

        # Ensure the target file exists (or will be created by the diff).
        # Git apply will handle creation of new files.
        _apply_diff(repo, diff_text)
        modified_files.append(target_path)

    # Stage and commit all modifications.
    commit_message = f"Promote experiment: {description}"
    _stage_and_commit(repo, modified_files, author_name, author_email, commit_message)

    # Handle optional version bump.
    _bump_version_if_needed(repo_root, changes)

    print(f"Experiment '{experiment_path.name}' promoted successfully.", file=sys.stderr)
import os
import subprocess
import json
import re
from typing import List, Dict, Any, Tuple

class ExperimentPromoter:
    """
    Handles promotion of a successful experiment into the main codebase.
    It:
    1. Extracts file changes recorded for the experiment.
    2. Applies them to the target files, resolving conflicts when multiple
       experiments modify the same file.
    3. Creates a git commit with proper attribution.
    4. Optionally bumps the project version if the changes are marked as
       significant.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = os.path.abspath(repo_path)

    # --------------------------------------------------------------------- #
    # 1. Load experiment diff information
    # --------------------------------------------------------------------- #
    def _load_experiment_diff(self, experiment_id: str) -> List[Dict[str, Any]]:
        """
        Expected format (JSON) for each experiment stored under
        ``experiments/<experiment_id>/diff.json``:

        [
            {
                "file": "relative/path/to/file.py",
                "type": "replace" | "insert_after" | "append",
                "search": "exact code to find",          # for replace
                "replace": "new code",                  # for replace
                "line": 42,                             # for insert_after
                "content": "new code to insert/append", # for insert/append
                "author": "Name <email>",
                "significant": true|false
            },
            ...
        ]
        """
        diff_path = os.path.join(
            self.repo_path,
            "experiments",
            experiment_id,
            "diff.json",
        )
        if not os.path.isfile(diff_path):
            raise FileNotFoundError(f"Diff file not found for experiment {experiment_id}")

        with open(diff_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # --------------------------------------------------------------------- #
    # 2. Apply changes with simple conflict detection
    # --------------------------------------------------------------------- #
    def _apply_change(self, change: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Apply a single change. Returns (conflict, message).
        """
        target_path = os.path.join(self.repo_path, change["file"])
        if not os.path.isfile(target_path):
            return True, f"Target file does not exist: {change['file']}"

        with open(target_path, "r", encoding="utf-8") as f:
            original = f.readlines()

        new_content = original[:]
        conflict = False
        msg = ""

        if change["type"] == "replace":
            # Find the exact block to replace
            search_block = change["search"]
            replace_block = change["replace"]
            # Build a regex that matches the block exactly (including newlines)
            pattern = re.escape(search_block)
            joined = "".join(new_content)
            if re.search(pattern, joined):
                new_joined = re.sub(pattern, replace_block, joined, count=1)
                new_content = new_joined.splitlines(keepends=True)
            else:
                conflict = True
                msg = f"Search block not found in {change['file']}"
        elif change["type"] == "insert_after":
            line_no = change["line"]
            if line_no < 0 or line_no > len(new_content):
                conflict = True
                msg = f"Invalid line number {line_no} for {change['file']}"
            else:
                insertion = change["content"]
                new_content.insert(line_no, insertion + ("\n" if not insertion.endswith("\n") else ""))
        elif change["type"] == "append":
            new_content.append(change["content"] + ("\n" if not change["content"].endswith("\n") else ""))
        else:
            conflict = True
            msg = f"Unsupported change type {change['type']}"

        if not conflict:
            with open(target_path, "w", encoding="utf-8") as f:
                f.writelines(new_content)

        return conflict, msg

    def _apply_changes(self, changes: List[Dict[str, Any]]) -> List[str]:
        """
        Apply all changes for an experiment. Returns a list of conflict messages,
        empty if everything succeeded.
        """
        conflicts = []
        for change in changes:
            conflict, msg = self._apply_change(change)
            if conflict:
                conflicts.append(msg)
        return conflicts

    # --------------------------------------------------------------------- #
    # 3. Create a git commit
    # --------------------------------------------------------------------- #
    def _git_commit(self, experiment_id: str, changes: List[Dict[str, Any]]) -> None:
        """
        Stage modified files and commit with a message that includes the
        experiment identifier and authorship.
        """
        # Stage files
        files_to_stage = {c["file"] for c in changes}
        subprocess.run(["git", "add"] + list(files_to_stage), cwd=self.repo_path, check=True)

        # Build commit message
        authors = {c.get("author", "unknown") for c in changes}
        author_str = ", ".join(authors)
        message = f"Promote experiment {experiment_id}\n\nAuthors: {author_str}"

        # Use the first author as the commit author (fallback to default)
        first_author = next(iter(authors))
        name_email_match = re.match(r"(.*)<(.*)>", first_author)
        if name_email_match:
            name, email = name_email_match.groups()
            env = os.environ.copy()
            env["GIT_AUTHOR_NAME"] = name.strip()
            env["GIT_AUTHOR_EMAIL"] = email.strip()
            env["GIT_COMMITTER_NAME"] = name.strip()
            env["GIT_COMMITTER_EMAIL"] = email.strip()
        else:
            env = None

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.repo_path,
            check=True,
            env=env,
        )

    # --------------------------------------------------------------------- #
    # 4. Optional version bump
    # --------------------------------------------------------------------- #
    def _bump_version(self) -> None:
        """
        Very simple version bump: look for a line like ``__version__ = "X.Y.Z"``
        in ``app/__init__.py`` and increment the patch number.
        """
        init_path = os.path.join(self.repo_path, "app", "__init__.py")
        if not os.path.isfile(init_path):
            return  # nothing to do

        with open(init_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        version_pattern = re.compile(r'(__version__\s*=\s*["\'])(\d+)\.(\d+)\.(\d+)(["\'])')
        new_lines = []
        bumped = False
        for line in lines:
            m = version_pattern.search(line)
            if m and not bumped:
                major, minor, patch = int(m.group(2)), int(m.group(3)), int(m.group(4))
                patch += 1
                new_version = f'{m.group(1)}{major}.{minor}.{patch}{m.group(5)}'
                new_lines.append(version_pattern.sub(new_version, line))
                bumped = True
            else:
                new_lines.append(line)

        if bumped:
            with open(init_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def promote(self, experiment_id: str) -> Tuple[bool, List[str]]:
        """
        Promote an experiment.
        Returns (success, messages). ``messages`` contains conflict info or
        success notes.
        """
        try:
            changes = self._load_experiment_diff(experiment_id)
        except Exception as e:
            return False, [f"Failed to load diff: {e}"]

        conflicts = self._apply_changes(changes)
        if conflicts:
            return False, conflicts

        # Determine if any change is marked as significant for version bump
        if any(c.get("significant", False) for c in changes):
            self._bump_version()

        # Commit the promotion
        try:
            self._git_commit(experiment_id, changes)
        except subprocess.CalledProcessError as e:
            return False, [f"Git commit failed: {e}"]

        return True, [f"Experiment {experiment_id} promoted successfully."]