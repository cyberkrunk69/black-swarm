"""
Scout doc-sync CLI — Documentation sync tool for generating and updating docs.

Generates documentation for Python, JavaScript, and other files via language adapters.
Auto-detects language by file extension; use --language to override.

Usage:
    ./devtools/scout-doc-sync generate --target vivarium/scout/router.py
    ./devtools/scout-doc-sync generate -t src/utils.js
    ./devtools/scout-doc-sync generate -t vivarium/scout/ -r -o docs/
"""

from __future__ import annotations

import argparse

from dotenv import load_dotenv

load_dotenv()

import asyncio
import sys
from pathlib import Path
from typing import Optional

from vivarium.scout.audit import AuditLog
from vivarium.scout.doc_generation import (
    BudgetExceededError,
    export_call_graph,
    export_knowledge_graph,
    find_stale_files,
    process_directory,
    process_single_file_async,
)
from vivarium.scout.git_analyzer import (
    get_changed_files,
    get_default_base_ref,
    get_git_commit_hash,
    get_git_version,
    get_upstream_ref,
)
from vivarium.scout.tools import query_for_deps


def _handle_generate(args: argparse.Namespace) -> int:
    """
    Handle the 'generate' subcommand.

    Resolves target path, validates it exists, and either runs dry-run
    preview or invokes doc_generation for file or directory.
    """
    target = args.target.resolve()
    if not target.exists():
        print(f"Error: Target does not exist: {target}", file=sys.stderr)
        return 1

    output_dir = args.output_dir.resolve() if args.output_dir else None
    recursive = args.recursive
    changed_only = getattr(args, "changed_only", False)

    if args.dry_run:
        _print_dry_run(target, output_dir, recursive)
        return 0

    audit = AuditLog()
    audit.log(
        "doc_sync",
        target=str(target),
        recursive=recursive,
        output_dir=str(output_dir) if output_dir else None,
        subcommand="generate",
    )

    generate_eliv = not getattr(args, "no_eliv", False)

    quiet = getattr(args, "quiet", False)

    try:
        force = getattr(args, "force", False)
        if target.is_file():
            versioned_dir = None
            if getattr(args, "versioned", False):
                repo_root = Path.cwd().resolve()
                ver = get_git_version(repo_root)
                versioned_dir = repo_root / "docs" / "livingDoc" / ver
            asyncio.run(
                process_single_file_async(
                    target,
                    output_dir=output_dir,
                    dependencies_func=query_for_deps,
                    language_override=getattr(args, "language", None),
                    generate_eliv=generate_eliv,
                    quiet=quiet,
                    force=force,
                    fallback_template=getattr(args, "fallback_template", False),
                    versioned_mirror_dir=versioned_dir,
                )
            )
            if versioned_dir is not None:
                version_file = Path.cwd().resolve() / "docs" / "livingDoc" / "VERSION"
                version_file.parent.mkdir(parents=True, exist_ok=True)
                commit = get_git_commit_hash(Path.cwd().resolve())
                ver = get_git_version(Path.cwd().resolve())
                version_file.write_text(
                    f"version: {ver}\ncommit: {commit}\n",
                    encoding="utf-8",
                )
                if not quiet:
                    print(f"Wrote {version_file}", file=sys.stderr)
        else:
            workers = getattr(args, "workers", None)
            budget = getattr(args, "budget", None)
            changed_files = None
            if changed_only:
                repo_root = Path.cwd().resolve()
                staged = getattr(args, "staged", False)
                if staged:
                    changed_files = get_changed_files(staged_only=True, repo_root=repo_root)
                else:
                    base = get_upstream_ref(repo_root) or get_default_base_ref(repo_root)
                    changed_files = (
                        get_changed_files(
                            staged_only=False,
                            repo_root=repo_root,
                            base_branch=base,
                        )
                        if base
                        else get_changed_files(staged_only=True, repo_root=repo_root)
                    )
                changed_files = [f for f in changed_files if f.suffix in (".py", ".js", ".mjs", ".cjs")]
            versioned_dir = None
            if getattr(args, "versioned", False):
                repo_root = Path.cwd().resolve()
                ver = get_git_version(repo_root)
                versioned_dir = repo_root / "docs" / "livingDoc" / ver
            process_directory(
                target,
                recursive=recursive,
                output_dir=output_dir,
                dependencies_func=query_for_deps,
                language_override=getattr(args, "language", None),
                workers=workers,
                generate_eliv=generate_eliv,
                quiet=quiet,
                budget=budget,
                force=force,
                changed_files=changed_files,
                fallback_template=getattr(args, "fallback_template", False),
                versioned_mirror_dir=versioned_dir,
            )
            if versioned_dir is not None:
                version_file = Path.cwd().resolve() / "docs" / "livingDoc" / "VERSION"
                version_file.parent.mkdir(parents=True, exist_ok=True)
                commit = get_git_commit_hash(Path.cwd().resolve())
                ver = get_git_version(Path.cwd().resolve())
                version_file.write_text(
                    f"version: {ver}\ncommit: {commit}\n",
                    encoding="utf-8",
                )
                if not quiet:
                    print(f"Wrote {version_file}", file=sys.stderr)
            if not getattr(args, "no_call_graph", False):
                repo_root = Path.cwd().resolve()
                vivarium_path = repo_root / "vivarium"
                t = target.resolve()
                if vivarium_path.exists() and (
                    t == vivarium_path or t == repo_root or str(vivarium_path).startswith(str(t))
                ):
                    out = vivarium_path / ".docs" / "call_graph.json"
                    export_call_graph(vivarium_path, output_path=out, repo_root=repo_root)
                    if not quiet:
                        print(f"Wrote {out}", file=sys.stderr)
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        audit.log(
            "doc_sync",
            reason="error",
            error=str(e),
        )
        return 1
    except BudgetExceededError as e:
        print(f"Error: {e}", file=sys.stderr)
        audit.log(
            "doc_sync",
            reason="budget_exceeded",
            total_cost=e.total_cost,
            budget=e.budget,
        )
        return 1

    audit.log(
        "doc_sync",
        target=str(target),
        subcommand="generate",
        status="complete",
    )
    return 0


def _print_dry_run(
    target: Path,
    output_dir: Optional[Path],
    recursive: bool,
) -> None:
    """Print what would be done without writing."""
    print(f"Dry run: would process target: {target}")
    if target.is_file():
        print(f"  Type: file")
        if output_dir is not None:
            print(f"  Output: {output_dir / target.stem}.tldr.md")
            print(f"  Output: {output_dir / target.stem}.deep.md")
            print(f"  Output: {(output_dir / target.name).with_suffix(target.suffix + '.eliv.md')}")
        else:
            local_docs = target.parent / ".docs"
            print(f"  Local:  {local_docs / target.name}.tldr.md")
            print(f"  Local:  {local_docs / target.name}.deep.md")
            print(f"  Local:  {local_docs / target.name}.eliv.md")
            try:
                rel = target.resolve().relative_to(Path.cwd().resolve())
                central = Path.cwd() / "docs" / "livingDoc" / rel.parent
                print(f"  Central: {central / target.name}.tldr.md")
                print(f"  Central: {central / target.name}.deep.md")
                print(f"  Central: {central / target.name}.eliv.md")
            except ValueError:
                pass
    else:
        patterns = ["**/*.py", "**/*.js", "**/*.mjs", "**/*.cjs"] if recursive else ["*.py", "*.js", "*.mjs", "*.cjs"]
        count = sum(1 for p in patterns for f in target.glob(p) if f.is_file())
        print(f"  Type: directory (recursive={recursive})")
        print(f"  Supported files: {count}")
        if output_dir is not None:
            print(f"  Output dir: {output_dir} (writes <stem>.tldr.md, <stem>.deep.md, <name>.eliv.md per file)")
        else:
            print(f"  Local: <source_dir>/.docs/<name>.tldr.md, .deep.md, and .eliv.md")
            print(f"  Central: docs/livingDoc/<path>/<name>.tldr.md, .deep.md, and .eliv.md")


def _handle_repair(args: argparse.Namespace) -> int:
    """Repair stale docs: find and reprocess files where meta hash mismatch."""
    target = args.target.resolve()
    if not target.exists():
        print(f"Error: Target does not exist: {target}", file=sys.stderr)
        return 1

    stale = find_stale_files(target, recursive=args.recursive)
    if not stale:
        print("No stale docs found.", file=sys.stdout)
        return 0

    cwd = Path.cwd()
    for f in stale:
        try:
            rel = str(f.relative_to(cwd))
        except ValueError:
            rel = str(f)
        print(f"Repaired stale doc: {rel}", file=sys.stdout)

    process_directory(
        target,
        recursive=args.recursive,
        dependencies_func=query_for_deps,
        workers=4,
        generate_eliv=False,
        quiet=args.quiet,
        budget=getattr(args, "budget", None),
        force=True,
        changed_files=stale,
    )
    return 1


def _handle_export(args: argparse.Namespace) -> int:
    """Export knowledge graph to JSON."""
    if not getattr(args, "kg", False):
        print("Use --kg to export knowledge graph.", file=sys.stderr)
        return 1
    target = args.target.resolve()
    if not target.exists():
        print(f"Error: Target does not exist: {target}", file=sys.stderr)
        return 1
    out = getattr(args, "output", None)
    path = export_knowledge_graph(target, output_path=out)
    print(f"Exported to {path}", file=sys.stdout)
    return 0


def _handle_validate(args: argparse.Namespace) -> int:
    """Validate docs: exit 1 if any stale (for CI)."""
    target = args.target.resolve()
    if not target.exists():
        print(f"Error: Target does not exist: {target}", file=sys.stderr)
        return 1

    stale = find_stale_files(target, recursive=args.recursive)
    if stale:
        cwd = Path.cwd()
        for f in stale:
            try:
                rel = str(f.relative_to(cwd))
            except ValueError:
                rel = str(f)
            print(f"Stale doc: {rel}", file=sys.stderr)
        print(f"Found {len(stale)} stale doc(s). Run: scout-doc-sync repair --stale", file=sys.stderr)
        return 1
    print("All docs up to date.", file=sys.stdout)
    return 0


def _handle_update(args: argparse.Namespace) -> int:
    """Handle the 'update' subcommand (future)."""
    print("update subcommand not yet implemented", file=sys.stderr)
    return 1


def _handle_status(args: argparse.Namespace) -> int:
    """Handle the 'status' subcommand (future)."""
    print("status subcommand not yet implemented", file=sys.stderr)
    return 1


def main() -> int:
    """
    Main entry point. Sets up parsers, parses arguments, and dispatches
    to the appropriate handler based on the subcommand.
    """
    parser = argparse.ArgumentParser(
        prog="scout-doc-sync",
        description="Scout: Documentation sync for Python, JavaScript, and more (plain-text fallback)",
        epilog="Models: Uses llama-3.1-8b-instant by default. Avoid groq/compound—use explicit models for predictable cost.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # generate subparser
    gen_parser = subparsers.add_parser("generate", help="Generate documentation")
    gen_parser.add_argument(
        "--target",
        "-t",
        type=Path,
        required=True,
        metavar="PATH",
        help="Required path (file or directory) to process",
    )
    gen_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=False,
        help="Process directory recursively (default: False if target is file)",
    )
    gen_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        metavar="DIR",
        help="Output directory (default: .docs/ next to source + docs/livingDoc/)",
    )
    gen_parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be done without writing",
    )
    gen_parser.add_argument(
        "--language",
        "-l",
        type=str,
        default=None,
        metavar="LANG",
        help="Override language (python, javascript, etc.). Auto-detect by default.",
    )
    gen_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        metavar="N",
        help="Max concurrent LLM calls (default: auto from model RPM)",
    )
    gen_parser.add_argument(
        "--no-eliv",
        action="store_true",
        help="Skip .eliv.md generation (bulk syncs). Overrides doc_generation.generate_eliv.",
    )
    gen_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode for CI: no live status, no per-file completion lines.",
    )
    gen_parser.add_argument(
        "--budget",
        type=float,
        default=None,
        metavar="N",
        help="Hard USD budget limit (e.g., 0.50). Stops all workers immediately when exceeded.",
    )
    gen_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Bypass freshness check; reprocess all files (ignore hash-based skip).",
    )
    gen_parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Only process files changed in git (staged or vs base branch).",
    )
    gen_parser.add_argument(
        "--staged",
        action="store_true",
        help="With --changed-only: use staged files only (for pre-commit).",
    )
    gen_parser.add_argument(
        "--no-call-graph",
        action="store_true",
        dest="no_call_graph",
        help="Skip call graph generation after full sync (default: generate when target is vivarium).",
    )
    gen_parser.add_argument(
        "--fallback-template",
        action="store_true",
        dest="fallback_template",
        help="When LLM fails or budget exceeded, generate docs via templates ([FALLBACK] header, cost 0).",
    )
    gen_parser.add_argument(
        "--versioned",
        action="store_true",
        dest="versioned",
        help="Mirror docs to docs/livingDoc/{version}/... and write docs/livingDoc/VERSION (version from git describe).",
    )

    # repair subparser
    repair_parser = subparsers.add_parser("repair", help="Repair stale docs")
    repair_parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path("vivarium"),
        metavar="PATH",
        help="Target path (default: vivarium)",
    )
    repair_parser.add_argument(
        "--stale",
        action="store_true",
        default=True,
        help="Find and reprocess stale docs (default)",
    )
    repair_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=True,
        help="Scan recursively (default)",
    )
    repair_parser.add_argument(
        "--budget",
        type=float,
        default=None,
        metavar="N",
        help="Hard USD budget limit",
    )
    repair_parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode",
    )

    # export subparser
    export_parser = subparsers.add_parser("export", help="Export knowledge graph")
    export_parser.add_argument(
        "--kg",
        action="store_true",
        help="Output vivarium.kg.json (nodes: files/funcs/classes, edges: calls/uses/exports)",
    )
    export_parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path("vivarium"),
        metavar="PATH",
        help="Target path (default: vivarium)",
    )
    export_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        metavar="FILE",
        help="Output file (default: vivarium.kg.json in target dir)",
    )

    # validate subparser
    validate_parser = subparsers.add_parser("validate", help="Validate docs (CI)")
    validate_parser.add_argument(
        "--target",
        "-t",
        type=Path,
        default=Path("vivarium"),
        metavar="PATH",
        help="Target path (default: vivarium)",
    )
    validate_parser.add_argument(
        "--stale",
        action="store_true",
        default=True,
        help="Check for stale docs; exit 1 if any (default)",
    )
    validate_parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        default=True,
        help="Scan recursively (default)",
    )

    # update subparser (future)
    subparsers.add_parser("update", help="Update existing docs (future)")

    # status subparser (future)
    subparsers.add_parser("status", help="Show sync status (future)")

    args = parser.parse_args()

    if args.command == "generate":
        return _handle_generate(args)
    if args.command == "repair":
        return _handle_repair(args)
    if args.command == "export":
        return _handle_export(args)
    if args.command == "validate":
        return _handle_validate(args)
    if args.command == "update":
        return _handle_update(args)
    if args.command == "status":
        return _handle_status(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
