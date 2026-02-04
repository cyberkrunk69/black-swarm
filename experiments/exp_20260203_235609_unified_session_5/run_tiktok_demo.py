#!/usr/bin/env python3
"""
run_tiktok_demo.py

Loads the 60‑second TikTok script and plays it back automatically.
Designed for screen‑recording – no user interaction required.
"""

import json
import time
import pathlib
import sys

def load_script(json_path: pathlib.Path):
    if not json_path.is_file():
        print(f"[Error] Script file not found: {json_path}", file=sys.stderr)
        sys.exit(1)
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("script", [])

def play_script(script):
    for entry in script:
        speaker = entry.get("speaker", "")
        text = entry.get("text", "")
        delay = float(entry.get("delay", 1))

        # Print line (skip empty speaker/text for pure pauses)
        if speaker or text:
            line = f"{speaker + ': ' if speaker else ''}{text}"
            print(line)
            # Flush so that screen‑recorders capture instantly
            sys.stdout.flush()
        else:
            # Pure pause – print a blank line for visual timing
            print()
            sys.stdout.flush()

        time.sleep(delay)

def main():
    # Path is relative to this script's location
    script_path = pathlib.Path(__file__).parent / "demo_scripts" / "tiktok_60s.json"
    script = load_script(script_path)
    print("\n--- Interdimensional Radio TikTok Demo (auto‑play) ---\n")
    play_script(script)
    print("\n--- End of Demo ---\n")

if __name__ == "__main__":
    main()