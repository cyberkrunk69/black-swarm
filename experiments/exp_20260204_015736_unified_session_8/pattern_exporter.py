import json
import csv
import os
from pathlib import Path

def export_patterns(
    json_path: str = "data/self_patterns.json",
    csv_path: str = "data/patterns_export.csv",
) -> None:
    """
    Export the self_patterns JSON file to a CSV file.

    The CSV will contain the following columns:
        - timestamp
        - type
        - details

    Parameters
    ----------
    json_path: str
        Path to the input JSON file (relative to the project root).
    csv_path: str
        Path where the CSV file will be written (relative to the project root).
    """
    # Resolve absolute paths based on the project root
    project_root = Path(__file__).resolve().parents[2]  # two levels up from this file
    json_file = project_root / json_path
    csv_file = project_root / csv_path

    if not json_file.is_file():
        raise FileNotFoundError(f"JSON source file not found: {json_file}")

    # Load JSON data
    with json_file.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to decode JSON from {json_file}: {exc}") from exc

    # Expecting a list of pattern objects
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array at top level in {json_file}")

    # Prepare CSV output
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "type", "details"])
        writer.writeheader()

        for idx, entry in enumerate(data):
            if not isinstance(entry, dict):
                raise ValueError(f"Entry {idx} is not an object: {entry}")

            # Extract required fields, defaulting to empty string if missing
            row = {
                "timestamp": entry.get("timestamp", ""),
                "type": entry.get("type", ""),
                "details": entry.get("details", ""),
            }
            writer.writerow(row)

    print(f"Exported {len(data)} patterns to {csv_file}")

if __name__ == "__main__":
    export_patterns()