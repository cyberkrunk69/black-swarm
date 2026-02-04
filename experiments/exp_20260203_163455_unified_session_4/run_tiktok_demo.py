import json
import time
import os
import sys

def load_script(json_path):
    """Load the TikTok demo script from the given JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['script']

def play_demo(script):
    """Print each line with the configured pause, simulating a 60‑second demo."""
    start_time = time.time()
    for entry in script:
        character = entry.get('character', 'Narrator')
        line = entry.get('line', '')
        pause = entry.get('pause_seconds', 2)

        # Print in a format that looks like a broadcast
        print(f"{character}: {line}")
        # Flush to ensure immediate display when screen‑recording
        sys.stdout.flush()
        time.sleep(pause)

    total_elapsed = time.time() - start_time
    # If we finished early, pad to exactly 60 seconds (optional)
    if total_elapsed < 60:
        time.sleep(60 - total_elapsed)

if __name__ == "__main__":
    # Resolve path relative to this script
    script_path = os.path.join(
        os.path.dirname(__file__),
        "demo_scripts",
        "tiktok_60s.json"
    )
    if not os.path.isfile(script_path):
        print(f"Error: script file not found at {script_path}")
        sys.exit(1)

    demo_script = load_script(script_path)
    play_demo(demo_script)