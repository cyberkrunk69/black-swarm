"""
# Ensure an index file exists for the dashboard.
import subprocess, pathlib, sys
def _ensure_index():
    idx_path = pathlib.Path(__file__).parent / "index.json"
    if not idx_path.exists():
        # generate a minimal empty index
        idx_path.write_text("[]", encoding="utf-8")
_ensure_index()
Package marker for benchmark result utilities.
"""