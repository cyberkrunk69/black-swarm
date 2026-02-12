"""
Scout CLI — Configuration management and navigation.

Usage:
    python -m vivarium.scout config                # Open in $EDITOR
    python -m vivarium.scout config --get triggers.default
    ./devtools/scripts/scout-nav --task "fix auth"  # Navigation CLI
"""

from vivarium.scout.cli.main import main

__all__ = ["main"]
