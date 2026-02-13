"""
Scout CLI — Configuration management.

Usage:
    python -m vivarium.scout config                # Open in $EDITOR
    python -m vivarium.scout config --get triggers.default
    python -m vivarium.scout config --set limits.hourly_budget 2.00
    python -m vivarium.scout config --tui          # Interactive TUI
    python -m vivarium.scout config --validate     # Check YAML syntax
    python -m vivarium.scout config --effective    # Show merged config
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from vivarium.scout.config import ScoutConfig
from vivarium.scout.router import TriggerRouter


def _cmd_config(args: argparse.Namespace) -> int:
    """Handle scout config subcommand."""
    config = ScoutConfig()

    if args.get:
        val = config.get(args.get)
        if val is None:
            print("(not set)", file=sys.stderr)
            return 1
        print(val)
        return 0

    if args.set:
        parts = args.set.split(maxsplit=1)
        if len(parts) != 2:
            print("Usage: --set KEY VALUE", file=sys.stderr)
            return 1
        key, value_str = parts[0], parts[1]
        # Try to parse as number
        try:
            value = float(value_str)
        except ValueError:
            value = value_str
        if config.set(key, value):
            print(f"Set {key} = {value}")
            return 0
        print(f"Failed to set {key}", file=sys.stderr)
        return 1

    if args.tui:
        from vivarium.scout.tui import run_config_tui

        return 0 if run_config_tui() else 1

    if args.validate:
        ok, msg = config.validate_yaml()
        if ok:
            print("Valid YAML")
            return 0
        print(f"Invalid: {msg}", file=sys.stderr)
        return 1

    if args.effective:
        print(json.dumps(config.to_dict(), indent=2, default=str))
        return 0

    # Default: open in editor
    path = config.get_project_config_path()
    if not path.exists():
        path = config.get_user_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            # Write defaults
            import yaml

            from vivarium.scout.config import DEFAULT_CONFIG

            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Failed to open editor: {e}", file=sys.stderr)
        return 1
    return 0


def _cmd_on_commit(args: argparse.Namespace) -> int:
    """Handle scout on-commit (git hook)."""
    files = args.files
    if not files and not sys.stdin.isatty():
        # Read from stdin if no args (e.g. from git hook piping)
        files = [f.strip() for f in sys.stdin.read().split() if f.strip()]
    # Git diff-tree outputs newline-separated; hook may pass as single arg
    expanded = []
    for f in files:
        expanded.extend(p.strip() for p in f.splitlines() if p.strip())
    paths = [Path(f) for f in expanded if f]
    router = TriggerRouter()
    router.on_git_commit(paths)
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="scout",
        description="Scout: zero-cost validation layer for LLM navigation",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_parser.add_argument(
        "--get",
        metavar="KEY",
        help="Print value (e.g. triggers.default)",
    )
    config_parser.add_argument(
        "--set",
        metavar="KEY VALUE",
        help="Set value (e.g. limits.hourly_budget 2.00)",
    )
    config_parser.add_argument(
        "--tui",
        action="store_true",
        help="Interactive terminal UI",
    )
    config_parser.add_argument(
        "--validate",
        action="store_true",
        help="Check YAML syntax",
    )
    config_parser.add_argument(
        "--effective",
        action="store_true",
        help="Show merged effective config",
    )

    on_commit_parser = subparsers.add_parser("on-commit", help="Git post-commit hook (process changed files)")
    on_commit_parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Changed files from git diff-tree",
    )

    args = parser.parse_args()

    if args.command == "on-commit":
        return _cmd_on_commit(args)
    if args.command == "config":
        return _cmd_config(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
