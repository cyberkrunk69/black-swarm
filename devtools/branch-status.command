#!/usr/bin/env bash
# One-click launcher for branch-status.sh (double-click in Finder)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
exec "$REPO_ROOT/devtools/branch-status.sh"
