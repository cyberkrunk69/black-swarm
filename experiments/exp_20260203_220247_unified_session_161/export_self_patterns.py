#!/usr/bin/env python3
"""
Utility to export `self_patterns.json` to a CSV file for offline analysis.

Usage:
    python export_self_patterns.py [--input INPUT_JSON] [--output OUTPUT_CSV]

If no arguments are provided, it assumes:
    - Input JSON: ./self_patterns.json (relative to the project root)
    - Output CSV: ./self_patterns.csv (placed alongside the JSON)
"""

import argparse
import csv
import json
import os
import sys
from collections import OrderedDict
from typing import List, Dict, Any, Set


def load_json(path: str) -> Any:
    """Load JSON data from a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading JSON file '{path}': {e}\\n")
        sys.exit(1)


def flatten_record(record: Any, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested dictionary/list structure into a single level dict.

    - Nested dicts become keys joined by `sep`.
    - Lists are enumerated with indices.
    """
    items: List[tuple] = []
    if isinstance(record, dict):
        for k, v in record.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.extend(flatten_record(v, new_key, sep=sep).items())
    elif isinstance(record, list):
        for idx, v in enumerate(record):
            new_key = f"{parent_key}{sep}{idx}" if parent_key else str(idx)
            items.extend(flatten_record(v, new_key, sep=sep).items())
    else:
        items.append((parent_key, record))
    return dict(items)


def collect_fieldnames(data: List[Dict[str, Any]]) -> List[str]:
    """Collect a deterministic ordering of all field names across records."""
    field_set: Set[str] = set()
    for rec in data:
        field_set.update(rec.keys())
    # Preserve insertion order: sort alphabetically for consistency
    return sorted(field_set)


def write_csv(data: List[Dict[str, Any]], fieldnames: List[str], output_path: str) -> None:
    """Write flattened data to CSV."""
    try:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in data:
                writer.writerow(row)
    except Exception as e:
        sys.stderr.write(f"Error writing CSV file '{output_path}': {e}\\n")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export self_patterns.json to CSV.")
    parser.add_argument(
        "--input",
        "-i",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "self_patterns.json"),
        help="Path to the input JSON file (default: ../../self_patterns.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "self_patterns.csv"),
        help="Path to the output CSV file (default: ../../self_patterns.csv)",
    )
    args = parser.parse_args()

    # Resolve paths relative to the project root
    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    # Load JSON
    raw_data = load_json(input_path)

    # Expecting a list of records; if it's a dict, wrap it in a list
    if isinstance(raw_data, dict):
        raw_data = [raw_data]
    elif not isinstance(raw_data, list):
        sys.stderr.write("JSON root must be an object or an array of objects.\\n")
        sys.exit(1)

    # Flatten each record
    flattened: List[Dict[str, Any]] = [flatten_record(rec) for rec in raw_data]

    # Determine CSV columns
    fieldnames = collect_fieldnames(flattened)

    # Write CSV
    write_csv(flattened, fieldnames, output_path)

    print(f"Export completed: {output_path}")


if __name__ == "__main__":
    main()