#!/usr/bin/env python3
"""
run_tiktok_demo.py
------------------
Automated 60‑second demo for the "Interdimensional Radio" TikTok cut.
It reads the scripted dialogue from demo_scripts/tiktok_60s.json,
prints each line with appropriate timing, and ends with the
standard "Link in bio" call‑to‑action.

Designed for screen‑recording: just launch the script and let it play.
"""

import json
import time
import sys
from pathlib import Path

def load_script(script_path: Path):
    """Load the JSON script containing dialogue entries."""
    with script_path.open('r', encoding='utf-8') as f:
        return json.load(f)

def play_dialogue(script):
    """Iterate through the script, printing each line and pausing."""
    for entry in script:
        speaker = entry.get("speaker", "Narrator")
        line = entry.get("line", "")
        pause = entry.get("pause", 3)  # default pause if missing

        # Print with speaker label
        print(f"{speaker}: {line}")
        sys.stdout.flush()

        # Sleep for the designated duration (seconds)
        time.sleep(pause)

def main():
    # Resolve paths relative to this file's location
    base_dir = Path(__file__).parent
    script_path = base_dir / "demo_scripts" / "tiktok_60s.json"

    if not script_path.is_file():
        print(f"Error: script not found at {script_path}", file=sys.stderr)
        sys.exit(1)

    script = load_script(script_path)
    print("\n--- Interdimensional Radio Demo (60 s) ---\n")
    play_dialogue(script)
    print("\n--- Demo finished ---\n")

if __name__ == "__main__":
    main()