#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second Interdimensional Radio demo.
Designed for screen‑recording: prints each line with timed pauses.
"""

import json
import time
import os
import sys

# Path to the script JSON (relative to this file)
SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "demo_scripts",
    "tiktok_60s.json"
)

def load_script(path: str):
    """Load the JSON script."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        sys.stderr.write(f"Error loading script: {e}\\n")
        sys.exit(1)

def play_demo(script):
    """Print each line with a pause based on the 'duration' field."""
    title = script.get("title", "Demo")
    print(f"=== {title} ===\\n")
    for entry in script.get("script", []):
        speaker = entry.get("speaker", "Narrator")
        line = entry.get("line", "")
        duration = entry.get("duration", 3)  # default 3 seconds if missing

        # Print with a simple format
        print(f"{speaker}: {line}")
        # Flush to ensure immediate display during recording
        sys.stdout.flush()
        # Pause for the designated duration (minimum 0.5s to keep flow)
        time.sleep(max(duration, 0.5))

    print("\\n--- Demo finished ---")
    sys.stdout.flush()

def main():
    script = load_script(SCRIPT_PATH)
    play_demo(script)

if __name__ == "__main__":
    main()