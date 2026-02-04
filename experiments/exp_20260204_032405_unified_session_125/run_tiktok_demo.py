import json
import time
import pathlib
import sys

def load_script(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        return json.load(f)

def play_demo(script):
    start_time = time.time()
    for entry in script:
        speaker = entry.get("speaker", "Narrator")
        line = entry.get("line", "")
        pause = entry.get("pause", 2)  # default pause between lines
        # Print with speaker tag
        print(f"{speaker}: {line}")
        # Ensure we don't exceed total 60 seconds by capping sleep
        elapsed = time.time() - start_time
        remaining = 60 - elapsed
        if remaining <= 0:
            break
        time_to_sleep = min(pause, remaining)
        time.sleep(time_to_sleep)

def main():
    # Resolve script location relative to this file
    script_path = pathlib.Path(__file__).parent / "demo_scripts" / "tiktok_60s.json"
    if not script_path.is_file():
        print(f"Script not found at {script_path}", file=sys.stderr)
        sys.exit(1)

    script = load_script(script_path)
    print("=== Starting 60‑second TikTok demo ===")
    play_demo(script)
    print("\n=== Demo finished ===")

if __name__ == "__main__":
    main()