#!/usr/bin/env python3
"""
run_tiktok_demo.py

A tiny self‑contained demo that auto‑plays a 60‑second scripted TikTok
conversation for the *Interdimensional Radio* concept.

It reads the JSON script from ./demo_scripts/tiktok_60s.json,
prints each line with the character name, and respects the
specified durations, so you can screen‑record the terminal output
without any user interaction.
"""

import json
import time
import os
import sys

def load_script(script_path: str):
    """Load the JSON script file."""
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load script: {e}")
        sys.exit(1)

def play_script(script):
    """Iterate over the script entries, printing and sleeping."""
    total_time = 0.0
    for entry in script:
        character = entry.get("character", "Narrator")
        line = entry.get("line", "")
        duration = float(entry.get("duration", 1))

        # Print with a simple formatting
        print(f"{character}: {line}")
        sys.stdout.flush()

        # Sleep for the duration (seconds)
        time.sleep(duration)
        total_time += duration

    # Final sanity check (should be ~60 seconds)
    print("\n--- Demo finished (≈{:.1f}s) ---".format(total_time))

def main():
    # Determine script location relative to this file
    base_dir = os.path.abspath(os.path.dirname(__file__))
    script_path = os.path.join(base_dir, "demo_scripts", "tiktok_60s.json")

    script = load_script(script_path)
    print("\n=== Interdimensional Radio – 60‑Second TikTok Demo ===\n")
    play_script(script)

if __name__ == "__main__":
    main()