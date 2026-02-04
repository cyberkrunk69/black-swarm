#!/usr/bin/env python3
"""
Utility to export `self_patterns.json` to CSV for offline analysis.

Usage:
    python export_self_patterns.py [input_json] [output_csv]

If no arguments are provided, it defaults to:
    input  : ./self_patterns.json
    output : ./self_patterns.csv
"""

import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Set


def load_json(json_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file expected to contain a list of objects."""
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON content must be a list of objects.")
    return data


def determine_fieldnames(records: List[Dict[str, Any]]) -> List[str]:
    """Collect a union of all keys across records, preserving order of first appearance."""
    fieldnames: List[str] = []
    seen: Set[str] = set()
    for rec in records:
        for key in rec.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    return fieldnames


def write_csv(records: List[Dict[str, Any]], csv_path: Path, fieldnames: List[str]) -> None:
    """Write records to a CSV file using the provided fieldnames."""
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            # Ensure all values are stringifiable; None becomes empty string
            sanitized = {k: ("" if v is None else v) for k, v in rec.items()}
            writer.writerow(sanitized)


def main(argv: List[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]

    # Default paths
    input_path = Path("self_patterns.json")
    output_path = Path("self_patterns.csv")

    if len(argv) >= 1:
        input_path = Path(argv[0])
    if len(argv) >= 2:
        output_path = Path(argv[1])

    try:
        records = load_json(input_path)
        if not records:
            print("No records found in JSON; creating an empty CSV with no rows.")
            fieldnames = []
        else:
            fieldnames = determine_fieldnames(records)

        write_csv(records, output_path, fieldnames)
        print(f"Successfully exported {len(records)} record(s) to CSV: {output_path}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())