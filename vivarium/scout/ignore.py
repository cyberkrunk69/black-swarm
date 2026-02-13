"""
Scout ignore patterns — loop prevention and self-protection.

Built-in patterns (cannot be disabled) + user .livingDocIgnore (gitignore-style).
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import List, Optional


# Built-in ignores: NEVER trigger on these (prevents infinite cascades)
BUILT_IN_IGNORES = [
    "~/.scout/audit.jsonl",  # Writing audit log must not trigger cascade
    ".livingDocIgnore",  # Root-level ignore file
    "**/.livingDocIgnore",  # Editing ignore file must not trigger (anywhere)
    "scout-config.yaml",  # Config edits must not trigger
    ".scout/config.yaml",  # Local config
    "docs/drafts/**",  # Output directory (results, not triggers)
    "**/.git/**",  # Git internals
    "**/__pycache__/**",  # Python cache
    "**/*.pyc",  # Compiled Python
    "**/node_modules/**",  # JS deps
]


def _glob_to_regex(pattern: str) -> str:
    """Convert glob pattern to regex. Supports * and **."""
    pattern = pattern.replace("\\", "/")
    result = []
    i = 0
    while i < len(pattern):
        if i + 1 < len(pattern) and pattern[i : i + 2] == "**":
            result.append("(?:[^/]+/)*[^/]*")
            i += 2
        elif pattern[i] == "*":
            result.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            result.append(".")
            i += 1
        else:
            result.append(re.escape(pattern[i]))
            i += 1
    return "^" + "".join(result) + "$"


def _normalize_path(path: Path, repo_root: Optional[Path] = None) -> str:
    """Normalize path for matching. Use forward slashes, resolve ~."""
    p = Path(path)
    if str(p).startswith("~"):
        p = p.expanduser()
    if repo_root and not p.is_absolute():
        p = (Path(repo_root) / p).resolve()
    return str(p).replace("\\", "/")


class IgnorePatterns:
    """
    Match paths against built-in + user ignore patterns.

    User patterns from .livingDocIgnore (gitignore-style):
    - ** globstar support
    - Negation with !
    - Standard fnmatch patterns
    """

    def __init__(self, repo_root: Optional[Path] = None, ignore_file: Optional[Path] = None):
        self._repo_root = Path(repo_root or Path.cwd()).resolve()
        self._ignore_file = ignore_file or (self._repo_root / ".livingDocIgnore")
        self._built_in: List[re.Pattern] = []
        self._positive: List[re.Pattern] = []
        self._negative: List[re.Pattern] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load built-in and user patterns."""
        self._built_in.clear()
        self._positive.clear()
        self._negative.clear()

        # Built-in (always active)
        for pat in BUILT_IN_IGNORES:
            norm = pat.replace("~", str(Path.home())).replace("\\", "/")
            self._built_in.append(re.compile(_glob_to_regex(norm)))

        # User .livingDocIgnore
        if self._ignore_file.exists():
            try:
                content = self._ignore_file.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    negated = line.startswith("!")
                    if negated:
                        line = line[1:].strip()
                    if not line:
                        continue
                    norm = line.replace("\\", "/")
                    regex = _glob_to_regex(norm)
                    if negated:
                        self._negative.append(re.compile(regex))
                    else:
                        self._positive.append(re.compile(regex))
            except OSError:
                pass

    def matches(self, path: Path, repo_root: Optional[Path] = None) -> bool:
        """
        Return True if path should be ignored (not trigger processing).

        Check order: built-in → positive user → negative user (negation overrides).
        """
        root = repo_root or self._repo_root
        norm = _normalize_path(path, root)

        # Also try path relative to repo
        try:
            rel = str(Path(path).resolve().relative_to(root)).replace("\\", "/")
        except ValueError:
            rel = norm

        for pat in self._built_in:
            if pat.search(norm) or pat.search(rel):
                return True

        # User patterns: positive = ignore, negative = don't ignore
        is_ignored_by_user = False
        for pat in self._positive:
            if pat.search(norm) or pat.search(rel):
                is_ignored_by_user = True
                break

        for pat in self._negative:
            if pat.search(norm) or pat.search(rel):
                is_ignored_by_user = False
                break

        return is_ignored_by_user

    def reload(self) -> None:
        """Reload patterns from disk (e.g. after .livingDocIgnore edit)."""
        self._load_patterns()
