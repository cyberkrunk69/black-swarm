#!/usr/bin/env bash
set -e

# Navigate to project root (assumes this script is in experiments/depth_4_test)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "Running Recursive Improvement Engine (depth‑4 test)..."
python recursive_improvement_engine.py > run_output.txt

echo "Comparing against expected output..."
if diff -u expected_output.md run_output.txt; then
    echo "Test passed."
else
    echo "Test failed – differences found."
    exit 1
fi