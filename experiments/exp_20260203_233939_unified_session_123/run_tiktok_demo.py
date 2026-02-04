#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second TikTok demo defined in
demo_scripts/tiktok_60s.json. Designed for screen‑recording:
- No user interaction required.
- Prints each line at the appropriate time.
- Ends with the “Link in bio” prompt.
"""

import json
import time
import pathlib
import sys

def load_script(json_path: pathlib.Path):
    if not json_path.is_file():
        sys.exit(f"❌ Script file not found: {json_path}")
    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("script", []), data.get("duration_seconds", 60)

def play_demo(script, total_duration):
    start_time = time.time()
    last_timestamp = 0

    for entry in script:
        # Calculate how long to wait before this line
        wait = entry["start"] - last_timestamp
        if wait > 0:
            time.sleep(wait)
        # Print the line with speaker label
        speaker = entry.get("speaker", "Narrator")
        line = entry.get("line", "")
        print(f"{speaker}: {line}")
        last_timestamp = entry["start"]

    # Ensure total runtime ≈ total_duration
    elapsed = time.time() - start_time
    remaining = total_duration - elapsed
    if remaining > 0:
        time.sleep(remaining)

    # Final prompt (redundant if already in script)
    print("\nLink in bio")

def main():
    # Paths are relative to this script's location
    base_dir = pathlib.Path(__file__).parent
    script_path = base_dir / "demo_scripts" / "tiktok_60s.json"

    script, duration = load_script(script_path)
    if not script:
        sys.exit("❌ Empty script – nothing to play.")
    print("=== Interdimensional Radio – 60‑Second TikTok Demo ===\n")
    play_demo(script, duration)
    print("\n=== Demo finished ===")

if __name__ == "__main__":
    main()