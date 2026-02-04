#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second TikTok demo defined in
demo_scripts/tiktok_60s.json. Designed for screen‑recording:
- No user interaction required.
- Prints each line with a short pause to simulate timing.
"""

import json
import time
import sys
from pathlib import Path

def load_script(json_path: Path):
    if not json_path.is_file():
        sys.exit(f"Script file not found: {json_path}")
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("script", [])

def play_demo(script):
    start = time.time()
    for entry in script:
        speaker = entry.get("speaker", "Unknown")
        text = entry.get("text", "")
        pause = float(entry.get("pause", 1))

        # Print with speaker prefix
        print(f"{speaker}: {text}", flush=True)

        # Sleep for the designated pause (but never let total exceed ~60s)
        elapsed = time.time() - start
        remaining = 60 - elapsed
        if remaining <= 0:
            break
        time.sleep(min(pause, remaining))

    # Ensure we finish close to 60 seconds
    total_elapsed = time.time() - start
    if total_elapsed < 60:
        time.sleep(60 - total_elapsed)

if __name__ == "__main__":
    script_path = Path(__file__).parent / "demo_scripts" / "tiktok_60s.json"
    demo_script = load_script(script_path)
    print("\n--- Starting Interdimensional Radio 60‑Second Demo ---\n")
    play_demo(demo_script)
    print("\n--- Demo finished. Remember: Link in bio! ---\n")