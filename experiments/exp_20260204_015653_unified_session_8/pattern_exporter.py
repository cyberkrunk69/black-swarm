import json
import csv
import os
from pathlib import Path

def load_self_patterns(json_path: Path) -> list:
    """Load self_patterns.json and return the list of pattern entries."""
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Expecting a list of dicts; if the JSON structure differs, adapt accordingly.
    if isinstance(data, dict) and "patterns" in data:
        data = data["patterns"]
    if not isinstance(data, list):
        raise ValueError("Unexpected JSON format: root element must be a list or contain 'patterns' key.")
    return data

def export_to_csv(patterns: list, csv_path: Path):
    """Export pattern list to CSV with columns: timestamp, type, details."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["timestamp", "type", "details"])
        writer.writeheader()
        for entry in patterns:
            # Safely extract fields; use empty string if missing.
            timestamp = entry.get("timestamp", "")
            ptype = entry.get("type", "")
            details = entry.get("details", "")
            # Ensure values are strings (CSV expects text)
            writer.writerow({
                "timestamp": str(timestamp),
                "type": str(ptype),
                "details": str(details)
            })

def main():
    # Paths are relative to the repository root (/app)
    json_path = Path(__file__).resolve().parents[2] / "data" / "self_patterns.json"
    csv_path = Path(__file__).resolve().parents[2] / "data" / "patterns_export.csv"

    try:
        patterns = load_self_patterns(json_path)
        export_to_csv(patterns, csv_path)
        print(f"Export successful: {csv_path}")
    except Exception as e:
        print(f"Error during export: {e}")

if __name__ == "__main__":
    main()