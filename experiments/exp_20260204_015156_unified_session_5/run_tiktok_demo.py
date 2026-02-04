#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second Interdimensional Radio demo defined in
demo_scripts/tiktok_60s.json. Designed for screen‑recording: it prints each
line with timed pauses, requiring no user interaction.
"""

import json
import time
import pathlib
import sys

def load_script(json_path: pathlib.Path):
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('script', []), data.get('total_duration_seconds', 60)

def play_demo(script):
    start = time.time()
    for entry in script:
        speaker = entry.get('speaker', 'Narrator')
        line = entry.get('line', '')
        duration = entry.get('duration', 5)

        # Print with a simple format
        print(f"{speaker}: {line}")
        # Flush so it appears instantly in recordings
        sys.stdout.flush()
        time.sleep(duration)

    elapsed = time.time() - start
    print(f"\n--- Demo finished (elapsed {elapsed:.1f}s) ---")
    sys.stdout.flush()

def main():
    base_dir = pathlib.Path(__file__).parent
    script_path = base_dir / "demo_scripts" / "tiktok_60s.json"

    if not script_path.is_file():
        print(f"Error: script file not found at {script_path}")
        sys.exit(1)

    script, total = load_script(script_path)

    # Simple sanity check: if total duration differs too much, warn but continue
    estimated = sum(entry.get('duration', 5) for entry in script)
    if abs(estimated - total) > 5:
        print(f"Warning: script total ({estimated}s) differs from declared total ({total}s).")

    print("=== Starting Interdimensional Radio 60‑second demo ===\n")
    play_demo(script)

if __name__ == "__main__":
    main()