#!/usr/bin/env python3
"""
Utility to export `self_patterns.json` to CSV for offline analysis.

Usage:
    python export_self_patterns.py [--input INPUT_JSON] [--output OUTPUT_CSV]

If no arguments are provided, it defaults to:
    INPUT_JSON  = ../self_patterns.json   (relative to the script location)
    OUTPUT_CSV  = self_patterns.csv
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, List, Dict


def load_json(path: str) -> Any:
    """Load JSON data from a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading JSON file '{path}': {e}\\n")
        sys.exit(1)


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested dictionary. Nested keys are concatenated with `sep`.
    Lists are left as-is (they will be converted to JSON strings later).
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def json_to_rows(data: Any) -> List[Dict[str, Any]]:
    """
    Convert loaded JSON data to a list of flat dictionaries suitable for CSV.
    Supports:
      - List of objects -> each object becomes a row.
      - Single object -> becomes a single row.
    """
    rows: List[Dict[str, Any]] = []

    if isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict):
                rows.append(flatten_dict(entry))
            else:
                # Primitive values are stored under a generic column
                rows.append({"value": entry})
    elif isinstance(data, dict):
        rows.append(flatten_dict(data))
    else:
        rows.append({"value": data})

    return rows


def write_csv(rows: List[Dict[str, Any]], output_path: str) -> None:
    """Write rows to a CSV file, inferring the header from all keys."""
    if not rows:
        sys.stderr.write("No data to write. The input JSON appears to be empty.\\n")
        return

    # Determine all unique field names across rows
    fieldnames = sorted({key for row in rows for key in row.keys()})

    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                # Ensure non‑string values are JSON‑encoded for readability
                clean_row = {
                    k: json.dumps(v) if isinstance(v, (list, dict)) else v
                    for k, v in row.items()
                }
                writer.writerow(clean_row)
        print(f"CSV exported successfully to: {output_path}")
    except Exception as e:
        sys.stderr.write(f"Error writing CSV file '{output_path}': {e}\\n")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export self_patterns.json to CSV.")
    parser.add_argument(
        "--input",
        "-i",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "self_patterns.json")),
        help="Path to the input JSON file (default: ../self_patterns.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "self_patterns.csv")),
        help="Path to the output CSV file (default: self_patterns.csv in script directory)",
    )
    args = parser.parse_args()

    json_data = load_json(args.input)
    rows = json_to_rows(json_data)
    write_csv(rows, args.output)


if __name__ == "__main__":
    main()