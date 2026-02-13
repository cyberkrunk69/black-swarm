"""
Git drafts — Assemble commit and PR drafts from docs/drafts/*.

Reads pre-generated drafts (from on-commit hooks or doc-sync).
No LLM calls. Agnostic: no IDE, no network, no state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

_MODULE_MD_NAME = "__init__.py.module.md"


def _stem_for_file(file_path: Path, root: Path) -> str:
    """Return stem for file path relative to repo root."""
    path = Path(file_path).resolve()
    try:
        return path.relative_to(root).stem
    except ValueError:
        return path.stem


def _find_package_root(file_path: Path, root: Path) -> Path | None:
    """Find the nearest package directory (with __init__.py) containing the file."""
    path = Path(file_path).resolve()
    try:
        parent = path.parent
        while parent != root and parent != root.parent:
            if (parent / "__init__.py").exists():
                return parent
            parent = parent.parent
        if (parent / "__init__.py").exists():
            return parent
    except (ValueError, OSError):
        pass
    return None


def _read_module_summary(repo_root: Path, package_dir: Path) -> str | None:
    """Read package __init__.py.module.md from central or local .docs/."""
    try:
        rel = package_dir.relative_to(repo_root)
    except ValueError:
        return None
    central = repo_root / "docs" / "livingDoc" / rel / _MODULE_MD_NAME
    if central.exists():
        try:
            return central.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            pass
    local = package_dir / ".docs" / _MODULE_MD_NAME
    if local.exists():
        try:
            return local.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            pass
    return None


def assemble_pr_description(repo_root: Path, staged_files: List[Path]) -> str:
    """
    Assemble a PR description from docs/drafts/{stem}.pr.md for each staged .py file.

    Enhanced with cascading context:
    - Groups changed files under their parent package headings
    - Includes package __init__.py.module.md summaries when available
    - Adds top-level "Architectural Impact" section using package summaries

    Args:
        repo_root: Repository root path.
        staged_files: List of staged file paths (absolute or relative to repo_root).

    Returns:
        Aggregated PR description as Markdown.
    """
    root = Path(repo_root).resolve()
    draft_dir = root / "docs" / "drafts"

    doc_extensions = {".py", ".js", ".mjs", ".cjs"}
    doc_files = [f for f in staged_files if Path(f).suffix in doc_extensions]
    if not doc_files:
        return "No staged doc files (.py, .js, .mjs, .cjs)."

    # Group files by package root; files without package go under root
    pkg_to_files: Dict[Path | None, List[Tuple[Path, str, str]]] = {}
    for file_path in doc_files:
        path = Path(file_path).resolve()
        stem = _stem_for_file(path, root)
        try:
            rel_str = str(path.relative_to(root))
        except ValueError:
            rel_str = path.name

        draft_path = draft_dir / f"{stem}.pr.md"
        if not draft_path.exists():
            draft_path = draft_dir / f"{stem}.pr.txt"
        if draft_path.exists():
            try:
                content = draft_path.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                content = "No PR draft available."
        else:
            content = "No PR draft available."

        pkg = _find_package_root(path, root)
        if pkg not in pkg_to_files:
            pkg_to_files[pkg] = []
        pkg_to_files[pkg].append((path, rel_str, content))

    # Gather package summaries for Architectural Impact
    package_summaries: List[Tuple[str, str]] = []
    for pkg in pkg_to_files:
        if pkg is None:
            continue
        summary = _read_module_summary(root, pkg)
        if summary:
            try:
                rel = str(pkg.relative_to(root))
            except ValueError:
                rel = str(pkg)
            package_summaries.append((rel, summary))

    sections: List[str] = []

    # Top-level Architectural Impact section
    if package_summaries:
        impact_parts = ["## Architectural Impact\n"]
        for rel, summary in package_summaries:
            impact_parts.append(f"### {rel}\n\n{summary}\n")
        sections.append("\n".join(impact_parts))

    # Per-package sections with changed files (sort: None last, then by path)
    def _pkg_key(p: Path | None) -> str:
        return str(p) if p is not None else "\xff"  # None sorts last

    for pkg in sorted(pkg_to_files.keys(), key=_pkg_key):
        files_data = pkg_to_files[pkg]
        if pkg is not None:
            try:
                pkg_rel = str(pkg.relative_to(root))
            except ValueError:
                pkg_rel = str(pkg)
            pkg_summary = _read_module_summary(root, pkg)
            block = [f"## {pkg_rel}\n"]
            if pkg_summary:
                block.append(pkg_summary)
                block.append("")
            block.append("### Changed Files\n")
            for _, rel_str, content in files_data:
                block.append(f"- **{Path(rel_str).name}**")
                if content:
                    block.append("")
                    block.append(content)
                block.append("")
            sections.append("\n".join(block).rstrip())
        else:
            block = ["## Other\n", "### Changed Files\n"]
            for _, rel_str, content in files_data:
                block.append(f"### {rel_str}\n\n{content}")
            sections.append("\n".join(block))

    return "\n\n---\n\n".join(sections)


def assemble_commit_message(repo_root: Path, staged_files: List[Path]) -> str:
    """
    Assemble a single commit message from docs/drafts/{stem}.commit.txt for each staged .py file.

    For each staged .py file, reads docs/drafts/{stem}.commit.txt if it exists.
    Falls back to "No draft available" if missing.
    Aggregates all into a single message (one section per file).

    Args:
        repo_root: Repository root path.
        staged_files: List of staged file paths (absolute or relative to repo_root).

    Returns:
        Aggregated commit message string.
    """
    root = Path(repo_root).resolve()
    draft_dir = root / "docs" / "drafts"
    sections: List[str] = []

    doc_extensions = {".py", ".js", ".mjs", ".cjs"}
    doc_files = [f for f in staged_files if Path(f).suffix in doc_extensions]
    if not doc_files:
        return "No staged doc files (.py, .js, .mjs, .cjs)."

    for file_path in doc_files:
        path = Path(file_path).resolve()
        stem = _stem_for_file(path, root)

        draft_path = draft_dir / f"{stem}.commit.txt"
        if draft_path.exists():
            try:
                content = draft_path.read_text(encoding="utf-8", errors="replace").strip()
                sections.append(content)
            except OSError:
                sections.append(f"[{path.name}]: No draft available")
        else:
            sections.append(f"[{path.name}]: No draft available")

    return "\n\n---\n\n".join(sections)
