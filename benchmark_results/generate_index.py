import os
import json

RESULTS_DIR = os.path.dirname(__file__)

def write_index():
    files = sorted([f for f in os.listdir(RESULTS_DIR) if f.startswith("run_") and f.endswith(".json")])
    index_path = os.path.join(RESULTS_DIR, "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(files, f, indent=2)

if __name__ == "__main__":
    write_index()