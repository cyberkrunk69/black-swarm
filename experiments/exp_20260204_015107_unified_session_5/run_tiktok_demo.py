#!/usr/bin/env python3
"""
run_tiktok_demo.py

A self‑contained script that automatically plays the 60‑second TikTok demo
described in demo_scripts/tiktok_60s.json.  It prints each line with the
appropriate timing so that the whole run lasts roughly 60 seconds, making it
ready for screen‑recording without any user interaction.
"""

import json
import time
import sys
from pathlib import Path

def load_script(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def print_line(entry):
    character = entry.get("character", "")
    line = entry.get("line", "")
    if character:
        output = f"{character}: {line}"
    else:
        output = line
    print(output)
    sys.stdout.flush()

def main():
    script_path = Path(__file__).parent / "demo_scripts" / "tiktok_60s.json"
    script = load_script(script_path)

    start_time = time.time()
    for entry in script:
        duration = max(float(entry.get("duration", 1)), 0.1)
        print_line(entry)
        time.sleep(duration)

    total = time.time() - start_time
    # Ensure we end close to 60 seconds (optional sanity check)
    if total < 58:
        time.sleep(60 - total)

if __name__ == "__main__":
    main()