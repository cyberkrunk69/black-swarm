"""
Scout tools — dependency resolution and utilities for doc generation.

Provides query_for_deps for use by doc_sync and doc_generation.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, List, Optional


def _module_to_path(repo_root: Path, mod: str) -> Optional[str]:
    """Resolve module name to repo-relative path if file exists."""
    if not mod or mod.startswith("."):
        return None
    path_str = mod.replace(".", "/")
    for candidate in [
        repo_root / f"{path_str}.py",
        repo_root / path_str / "__init__.py",
    ]:
        if candidate.exists():
            try:
                return str(candidate.relative_to(repo_root))
            except ValueError:
                pass
    return None


def _parse_imports(content: str, repo_root: Path) -> List[str]:
    """Extract import targets and resolve to repo paths where possible."""
    import_re = re.compile(
        r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))\s"
    )
    results: List[str] = []
    seen: set = set()
    for line in content.splitlines():
        m = import_re.match(line)
        if m:
            mod = (m.group(1) or m.group(2) or "").split()[0]
            if not mod or mod.startswith("."):
                continue
            path = _module_to_path(repo_root, mod)
            if path and path not in seen:
                seen.add(path)
                results.append(path)
    return results[:15]


def query_for_deps(path: Path) -> List[str]:
    """
    Resolve dependencies for a Python file path.

    Returns a list of repo-relative paths that the given file imports.
    Used by doc_generation for dependency-aware documentation.

    Args:
        path: Absolute path to a Python file.

    Returns:
        List of repo-relative dependency paths.
    """
    repo_root = Path.cwd().resolve()
    try:
        target_file = str(path.resolve().relative_to(repo_root))
    except ValueError:
        return []
    fp = repo_root / target_file
    if not fp.exists() or not fp.is_file() or fp.suffix != ".py":
        return []
    try:
        content = fp.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return _parse_imports(content, repo_root)
