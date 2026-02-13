"""
Scout root CLI — Top-level entry for scout-commit, scout-pr, and related commands.

Usage:
    python -m vivarium.scout.cli.root commit --preview
    python -m vivarium.scout.cli.root commit --use-draft
    python -m vivarium.scout.cli.root pr --preview
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from vivarium.scout.doc_generation import (
    find_stale_files,
    get_downstream_impact,
    synthesize_pr_description,
)
from vivarium.scout.git_analyzer import (
    get_changed_files,
    get_current_branch,
    get_default_base_ref,
    get_upstream_ref,
    has_remote_origin,
    is_remote_empty,
)
from vivarium.scout.git_drafts import assemble_commit_message, assemble_pr_description

# File extensions supported for PR drafts (matches git_drafts.assemble_pr_description)
_DOC_EXTENSIONS = {".py", ".js", ".mjs", ".cjs"}


def _resolve_pr_files(
    args: argparse.Namespace, repo_root: Path
) -> tuple[list[Path], str]:
    """
    Resolve which files to include in PR description.

    Priority:
    1. --files / -f: explicit list (bypasses Git diff)
    2. --base-branch: git diff --name-only base...HEAD
    3. upstream: git diff --name-only @{upstream}..HEAD (if on branch with upstream)
    4. origin/main or origin/master: git diff vs default remote branch
    5. staged: git diff --cached (with warning if origin/main, origin/master unavailable)

    Returns:
        (list of resolved file paths, mode string for error messages)
    """
    root = repo_root.resolve()

    if args.files:
        resolved: list[Path] = []
        for fp in args.files:
            p = Path(fp)
            if not p.is_absolute():
                p = (root / p).resolve()
            else:
                p = p.resolve()
            if not p.exists():
                print(f"Warning: skipping non-existent file: {fp}", file=sys.stderr)
                continue
            resolved.append(p)
        files = [f for f in resolved if f.suffix in _DOC_EXTENSIONS]
        return files, "explicit file list (--files)"

    if args.base_branch:
        changed = get_changed_files(
            staged_only=False,
            repo_root=repo_root,
            base_branch=args.base_branch,
        )
        files = [f for f in changed if f.suffix in _DOC_EXTENSIONS]
        return files, f"git diff --base-branch {args.base_branch}"

    upstream = get_upstream_ref(repo_root)
    if upstream:
        changed = get_changed_files(
            staged_only=False,
            repo_root=repo_root,
            base_branch=upstream,
        )
        files = [f for f in changed if f.suffix in _DOC_EXTENSIONS]
        return files, f"git diff @{{upstream}}..HEAD ({upstream})"

    default_base = get_default_base_ref(repo_root)
    if default_base:
        changed = get_changed_files(
            staged_only=False,
            repo_root=repo_root,
            base_branch=default_base,
        )
        files = [f for f in changed if f.suffix in _DOC_EXTENSIONS]
        return files, f"git diff {default_base}..HEAD"

    print(
        "Warning: No upstream configured and origin/main, origin/master not found. "
        "Using staged files.",
        file=sys.stderr,
    )
    staged = get_changed_files(staged_only=True, repo_root=repo_root)
    files = [f for f in staged if f.suffix in _DOC_EXTENSIONS]
    return files, "staged files"


def _cmd_commit(args: argparse.Namespace) -> int:
    """
    Handle scout commit subcommand.

    Uses git_analyzer.get_changed_files(staged_only=True), filters for .py files,
    reads docs/drafts/{stem}.commit.txt per file, aggregates into a single message.
    If --preview: prints to stdout. Else: writes to temp file and runs git commit -F <temp>.
    """
    repo_root = Path.cwd().resolve()
    staged = get_changed_files(staged_only=True, repo_root=repo_root)
    py_files = [f for f in staged if f.suffix == ".py"]

    if not py_files:
        print("No staged files.", file=sys.stderr)
        return 1

    if not args.use_draft:
        # Run git commit without draft (opens editor)
        try:
            subprocess.run(["git", "commit"], check=True, cwd=repo_root)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    message = assemble_commit_message(repo_root, py_files)

    if args.preview:
        print(message)
        return 0

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(message)
            tmp_path = f.name
        try:
            subprocess.run(
                ["git", "commit", "-F", tmp_path],
                check=True,
                cwd=repo_root,
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def _cmd_pr_auto_draft(
    repo_root: Path,
    py_files: list[Path],
    mode: str,
) -> int:
    """
    Generate PR description and write to .github/pr-draft.md.
    Includes: changed files summary, architectural impact, cost audit, stale status,
    and impact analysis from call graph.
    Idempotent: safe to run multiple times.
    """
    out_path = repo_root / ".github" / "pr-draft.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build description from drafts or raw summaries
    if py_files:
        raw = assemble_pr_description(repo_root, py_files)
        description = synthesize_pr_description(raw)
    else:
        description = "# PR Draft\n\nNo changed files in scope.\n"

    # Versioned docs link if available
    version_file = repo_root / "docs" / "livingDoc" / "VERSION"
    if version_file.exists():
        try:
            content = version_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("version:"):
                    ver = line.split(":", 1)[1].strip()
                    description += f"\n[Docs {ver}](/docs/livingDoc/{ver}/)\n"
                    break
        except OSError:
            pass

    # Impact section from call graph
    call_graph_path = repo_root / "vivarium" / ".docs" / "call_graph.json"
    if call_graph_path.exists() and py_files:
        impact_modules = get_downstream_impact(py_files, call_graph_path, repo_root)
        if impact_modules:
            modules_str = ", ".join(impact_modules)
            impact_section = (
                f"\n## Impact\n\n"
                f"This change affects {len(impact_modules)} module(s): {modules_str}. "
                f"Their docs were auto-refreshed.\n"
            )
            description += impact_section

    # Append stale status
    vivarium_path = repo_root / "vivarium"
    if vivarium_path.exists():
        stale = find_stale_files(vivarium_path, recursive=True)
        if stale:
            try:
                rels = [str(f.relative_to(repo_root)) for f in stale[:10]]
            except ValueError:
                rels = [str(f) for f in stale[:10]]
            extra = f"\n\n---\n**Stale docs** ({len(stale)}): run `scout-doc-sync repair --stale`\n"
            if len(stale) <= 10:
                extra += "\n".join(f"- {r}" for r in rels) + "\n"
            else:
                extra += "\n".join(f"- {r}" for r in rels) + f"\n- ... and {len(stale) - 10} more\n"
            description += extra
        else:
            description += "\n\n---\n**Docs**: All up to date.\n"

    out_path.write_text(description, encoding="utf-8")
    print(f"Wrote {out_path}", file=sys.stderr)
    return 0


def _find_gh() -> str | None:
    """Return path to gh CLI if installed, else None."""
    try:
        result = subprocess.run(
            ["which", "gh"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _cmd_pr(args: argparse.Namespace) -> int:
    """
    Handle scout pr subcommand.

    File resolution (in order):
    - --files / -f: use explicit file list (bypasses Git diff)
    - --base-branch: use git diff --name-only base...HEAD
    - upstream: use git diff --name-only @{upstream}..HEAD (if on branch with upstream)
    - default: use staged files

    Reads docs/drafts/{stem}.pr.md per file, aggregates into a single PR description.
    If --preview: prints to stdout. If --create: runs gh pr create. If --auto-draft: writes .github/pr-draft.md.
    """
    repo_root = Path.cwd().resolve()
    py_files, mode = _resolve_pr_files(args, repo_root)

    if args.auto_draft:
        return _cmd_pr_auto_draft(repo_root, py_files, mode)

    if not py_files:
        print(f"No Python/JS files found in {mode}.", file=sys.stderr)
        return 1

    if not args.use_draft:
        print("Skipping draft assembly (--no-use-draft).", file=sys.stderr)
        return 0

    raw_description = assemble_pr_description(repo_root, py_files)
    description = synthesize_pr_description(raw_description)

    if args.create:
        if not _find_gh():
            print("Install GitHub CLI: https://cli.github.com", file=sys.stderr)
            return 1

        branch = get_current_branch(repo_root)
        title = branch.replace("-", " ").replace("_", " ").title() if branch else "Scout PR"

        # Determine PR create mode: empty remote, first push, or normal
        gh_base: str | None = None
        if has_remote_origin(repo_root) and is_remote_empty(repo_root):
            # Empty remote: push HEAD to initialize, PR against self (GitHub allows)
            if not branch:
                print("Error: Cannot create PR from detached HEAD. Check out a branch first.", file=sys.stderr)
                return 1
            print(f"Initializing remote repo by pushing '{branch}'...", file=sys.stderr)
            try:
                subprocess.run(
                    ["git", "push", "-u", "origin", "HEAD"],
                    capture_output=True,
                    text=True,
                    check=True,
                    cwd=repo_root,
                )
            except subprocess.CalledProcessError as e:
                msg = getattr(e, "stderr", None) or str(e)
                print(f"Error: git push failed: {msg}", file=sys.stderr)
                return 1
            gh_base = branch
        else:
            # First PR case: no upstream, origin/main fails, origin exists, not on main/master
            needs_push = (
                not get_upstream_ref(repo_root)
                and not get_default_base_ref(repo_root)
                and has_remote_origin(repo_root)
                and branch
                and branch not in ("main", "master")
            )
            if needs_push:
                print(f"Pushing branch '{branch}' to origin...", file=sys.stderr)
                try:
                    subprocess.run(
                        ["git", "push", "-u", "origin", branch],
                        capture_output=True,
                        text=True,
                        check=True,
                        cwd=repo_root,
                    )
                except subprocess.CalledProcessError as e:
                    msg = getattr(e, "stderr", None) or str(e)
                    print(f"Error: git push failed: {msg}", file=sys.stderr)
                    return 1
                gh_base = "main"

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(description)
                body_path = f.name
            try:
                gh_args = ["gh", "pr", "create", "--title", title]
                if gh_base:
                    gh_args.extend(["--base", gh_base])
                gh_args.extend(["--body-file", body_path])
                subprocess.run(
                    gh_args,
                    check=True,
                    cwd=repo_root,
                )
            finally:
                Path(body_path).unlink(missing_ok=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    print(description)
    return 0


def main() -> int:
    """Main entry point for scout root CLI."""
    parser = argparse.ArgumentParser(
        prog="scout-root",
        description="Scout: Commit and PR draft assembly from docs/drafts/*",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    commit_parser = subparsers.add_parser("commit", help="Commit using assembled drafts")
    commit_parser.add_argument(
        "--use-draft",
        action="store_true",
        default=True,
        dest="use_draft",
        help="Use docs/drafts/*.commit.txt for message (default: True)",
    )
    commit_parser.add_argument(
        "--no-use-draft",
        action="store_false",
        dest="use_draft",
        help="Skip draft assembly, run git commit (opens editor)",
    )
    commit_parser.add_argument(
        "--preview",
        action="store_true",
        help="Print assembled message to stdout without committing",
    )

    pr_parser = subparsers.add_parser("pr", help="PR description from assembled drafts")
    pr_parser.add_argument(
        "--files",
        "-f",
        nargs="+",
        dest="files",
        default=None,
        help="Explicit list of files to include in PR description (bypasses Git diff)",
    )
    pr_parser.add_argument(
        "--base-branch",
        dest="base_branch",
        default=None,
        metavar="BRANCH",
        help="Base branch for git diff (e.g. origin/main). Uses git diff --name-only base...HEAD",
    )
    pr_parser.add_argument(
        "--use-draft",
        action="store_true",
        default=True,
        dest="use_draft",
        help="Use docs/drafts/*.pr.md for description (default: True)",
    )
    pr_parser.add_argument(
        "--no-use-draft",
        action="store_false",
        dest="use_draft",
        help="Skip draft assembly",
    )
    pr_parser.add_argument(
        "--preview",
        action="store_true",
        help="Print PR description to stdout (always prints; no browser)",
    )
    pr_parser.add_argument(
        "--create",
        action="store_true",
        help="Create PR via gh CLI (gh pr create --title ... --body-file ...)",
    )
    pr_parser.add_argument(
        "--auto-draft",
        action="store_true",
        help="Generate PR description and write to .github/pr-draft.md (idempotent)",
    )

    subparsers.add_parser("status", help="Workflow dashboard (doc-sync, drafts, spend, accuracy, hooks)")

    args = parser.parse_args()

    if args.command == "commit":
        return _cmd_commit(args)
    if args.command == "pr":
        return _cmd_pr(args)
    if args.command == "status":
        from vivarium.scout.cli.status import run_status

        print(run_status(Path.cwd().resolve()))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
