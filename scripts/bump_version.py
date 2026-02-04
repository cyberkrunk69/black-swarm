#!/usr/bin/env python3
"""
Automated semantic version bump for claude_parasite_brain_suck.
Usage:
    python scripts/bump_version.py [major|minor|patch]
If no argument is supplied, the patch version is incremented.
"""

import re
import sys
from pathlib import Path

VERSION_FILE = Path(__file__).resolve().parents[1] / "brain" / "__init__.py"

def read_version():
    content = VERSION_FILE.read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        raise RuntimeError("Version string not found.")
    return match.group(1), content

def write_version(new_version, original_content):
    new_content = re.sub(r'(__version__\s*=\s*")[^"]+(")', rf'\1{new_version}\2', original_content)
    VERSION_FILE.write_text(new_content)
    print(f"Version bumped to {new_version}")

def bump(version, part):
    major, minor, patch = map(int, version.split('.'))
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    return f"{major}.{minor}.{patch}"

if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if part not in {"major", "minor", "patch"}:
        print("Invalid argument. Use major, minor, or patch.")
        sys.exit(1)

    current_version, content = read_version()
    new_version = bump(current_version, part)
    write_version(new_version, content)