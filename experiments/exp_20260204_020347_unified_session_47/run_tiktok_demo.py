#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second Interdimensional Radio demo.
Designed for screen‑recording: prints each line with a pause,
so the output runs in real‑time without any user interaction.
"""

import json
import time
import pathlib
import sys

def load_script(json_path: pathlib.Path):
    if not json_path.is_file():
        sys.exit(f"Script file not found: {json_path}")
    with json_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("script", [])

def play_demo(script):
    start_time = time.time()
    for entry in script:
        character = entry.get("character", "Narrator")
        text = entry.get("text", "")
        pause = entry.get("pause", 2)  # default 2 seconds if omitted

        # Print in a TikTok‑style caption format
        print(f"{character}: {text}")
        # Flush to ensure immediate display when screen‑recording
        sys.stdout.flush()

        # Sleep only if there is remaining time (prevents overshoot)
        elapsed = time.time() - start_time
        remaining = pause - elapsed % pause
        if remaining > 0:
            time.sleep(remaining)
    total = time.time() - start_time
    print(f"\n--- Demo finished (≈{int(total)} seconds) ---")

def main():
    # Resolve the JSON script relative to this file
    base_dir = pathlib.Path(__file__).parent
    script_path = base_dir / "demo_scripts" / "tiktok_60s.json"
    script = load_script(script_path)
    if not script:
        sys.exit("No script entries found.")
    play_demo(script)

if __name__ == "__main__":
    main()