"""Allow running as python -m vivarium.scout."""

from vivarium.scout.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
