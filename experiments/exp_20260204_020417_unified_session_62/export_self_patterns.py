#!/usr/bin/env python3
"""
Utility to export `self_patterns.json` to a CSV file for offline analysis.

Usage:
    python export_self_patterns.py [--input INPUT_JSON] [--output OUTPUT_CSV]

If no arguments are provided, the script assumes:
    INPUT_JSON  = "./self_patterns.json"
    OUTPUT_CSV  = "./self_patterns.csv"
"""

import argparse
import csv
import json
import os
import sys
from collections import OrderedDict
from typing import Any, List, Dict, Set


def load_json(path: str) -> Any:
    """Load JSON data from a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        sys.stderr.write(f"Error loading JSON from {path}: {exc}\\n")
        sys.exit(1)


def flatten_record(record: Any, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """
    Flatten a nested JSON object into a single dict with dot‑separated keys.
    Handles dicts and lists (list items are indexed).
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


def collect_headers(data: List[Dict[str, Any]]) -> List[str]:
    """Collect a deterministic list of CSV headers from flattened records."""
    header_set: Set[str] = set()
    for rec in data:
        header_set.update(rec.keys())
    # Preserve order: sorted alphabetically for reproducibility
    return sorted(header_set)


def write_csv(data: List[Dict[str, Any]], headers: List[str], out_path: str) -> None:
    """Write flattened data to CSV."""
    try:
        with open(out_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for rec in data:
                writer.writerow(rec)
    except Exception as exc:
        sys.stderr.write(f"Error writing CSV to {out_path}: {exc}\\n")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export self_patterns.json to CSV.")
    parser.add_argument(
        "--input",
        "-i",
        default=os.path.join(os.getcwd(), "self_patterns.json"),
        help="Path to the input JSON file (default: ./self_patterns.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=os.path.join(os.getcwd(), "self_patterns.csv"),
        help="Path for the generated CSV file (default: ./self_patterns.csv)",
    )
    args = parser.parse_args()

    raw_data = load_json(args.input)

    # Determine how to treat the JSON structure:
    #   - If it's a list, each element becomes a row.
    #   - If it's a dict, we treat its values as rows if they are list/dict,
    #     otherwise we output a single row.
    if isinstance(raw_data, list):
        records = raw_data
    elif isinstance(raw_data, dict):
        # Prefer a top‑level list under a known key, else treat dict values as rows.
        if any(isinstance(v, list) for v in raw_data.values()):
            # Find the first list value
            list_val = next(v for v in raw_data.values() if isinstance(v, list))
            records = list_val
        else:
            records = [raw_data]
    else:
        sys.stderr.write("Unsupported JSON root type. Must be list or dict.\\n")
        sys.exit(1)

    # Flatten each record for CSV compatibility
    flattened = [flatten_record(rec) for rec in records]

    # Determine CSV headers
    headers = collect_headers(flattened)

    # Write out CSV
    write_csv(flattened, headers, args.output)

    print(f"Export completed: {args.output}")


if __name__ == "__main__":
    main()