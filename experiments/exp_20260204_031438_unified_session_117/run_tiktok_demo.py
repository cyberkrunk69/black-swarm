#!/usr/bin/env python3
"""
run_tiktok_demo.py

Loads the 60‑second TikTok script and plays it automatically.
Designed for screen‑recording – no user interaction required.
"""

import json
import time
import os
import sys

SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "demo_scripts",
    "tiktok_60s.json"
)

def load_script(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def print_line(character: str, line: str):
    # Simple formatting – you can style this further if you like.
    print(f"{character}: {line}")

def main():
    script_data = load_script(SCRIPT_PATH)
    total_time = 0.0

    print("\n--- Interdimensional Radio Demo (60‑second TikTok Cut) ---\n")
    for entry in script_data["script"]:
        delay = entry.get("delay_before", 0)
        time.sleep(delay)
        total_time += delay
        print_line(entry["character"], entry["line"])
        # Small pause after printing to simulate natural speech timing
        time.sleep(0.5)
        total_time += 0.5

    # Fill any remaining time to reach ~60 seconds (optional)
    remaining = 60 - total_time
    if remaining > 0:
        time.sleep(remaining)

    print("\nLink in bio 🌟\n")
    # Keep the terminal open for a moment so the recorder catches the final line
    time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)