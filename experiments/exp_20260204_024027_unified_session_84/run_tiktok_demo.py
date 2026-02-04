#!/usr/bin/env python3
"""
run_tiktok_demo.py

Automatically plays the 60‑second Interdimensional Radio demo defined in
`demo_scripts/tiktok_60s.json`.  The script is self‑contained, requires no
user interaction, and is suitable for screen‑recording.
"""

import json
import time
import pathlib
import sys

SCRIPT_PATH = pathlib.Path(__file__).parent / "demo_scripts" / "tiktok_60s.json"


def load_script(path: pathlib.Path):
    if not path.is_file():
        sys.stderr.write(f"Script file not found: {path}\\n")
        sys.exit(1)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def play_demo(script_data):
    title = script_data.get("title", "Demo")
    total_duration = script_data.get("duration_seconds", 60)
    script = script_data.get("script", [])

    print(f"=== {title} ===\\n")
    start_time = time.time()
    elapsed = 0

    for entry in script:
        character = entry.get("character", "Narrator")
        line = entry.get("line", "")
        delay = entry.get("delay_seconds", 0)

        # Show the line
        print(f"{character}: {line}")

        # Wait the specified delay (but never exceed the total duration)
        if delay > 0:
            time.sleep(delay)
            elapsed = time.time() - start_time
            if elapsed >= total_duration:
                break

    # Fill remaining time (if any) to reach approx. 60 seconds
    remaining = total_duration - (time.time() - start_time)
    if remaining > 0:
        time.sleep(remaining)

    # Final prompt
    print("\\nLink in bio!")


def main():
    script_data = load_script(SCRIPT_PATH)
    play_demo(script_data)


if __name__ == "__main__":
    main()