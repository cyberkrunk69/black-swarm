# cli.py

## Function: `_cmd_config`

Detailed documentation (deep stub).

```python
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
        key, value_str = par
```

## Function: `_cmd_on_commit`

Detailed documentation (deep stub).

```python
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
    paths
```

## Function: `main`

Detailed documentation (deep stub).

```python
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
    config_parser.add_a
```
