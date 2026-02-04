"""
Dashboard Rebuild Module
========================

This module provides utilities to rebuild the web dashboard for the
Claude Parasite Brain Suck project. It aggregates data sources,
processes metrics, and renders the updated UI components.

Typical usage:

    from dashboard import rebuild_dashboard

    # Rebuild the entire dashboard
    rebuild_dashboard()

"""

import os
import json
import logging
from typing import Dict, Any

# Configure a simple logger for the dashboard rebuild process
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def load_data(source_path: str) -> Dict[str, Any]:
    """
    Load JSON data from the specified source path.

    Args:
        source_path: Path to a JSON file containing raw data.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        FileNotFoundError: If the source file does not exist.
        json.JSONDecodeError: If the file contents are not valid JSON.
    """
    logger.info(f"Loading data from {source_path}")
    if not os.path.isfile(source_path):
        raise FileNotFoundError(f"Data source not found: {source_path}")

    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.debug(f"Loaded data: {data}")
    return data


def process_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform raw data into dashboard metrics.

    This is a placeholder implementation; replace with real logic as needed.

    Args:
        raw_data: Raw data dictionary.

    Returns:
        Processed metrics dictionary.
    """
    logger.info("Processing metrics")
    # Example transformation: count entries per category
    metrics = {}
    for entry in raw_data.get("entries", []):
        category = entry.get("category", "unknown")
        metrics[category] = metrics.get(category, 0) + 1

    logger.debug(f"Processed metrics: {metrics}")
    return metrics


def render_dashboard(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Render the dashboard HTML file using the computed metrics.

    Args:
        metrics: Dictionary of processed metrics.
        output_path: Destination path for the generated HTML file.
    """
    logger.info(f"Rendering dashboard to {output_path}")
    html_template = f\"\"\"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Claude Parasite Brain Suck Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2rem; }}
        table {{ border-collapse: collapse; width: 60%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Dashboard Overview</h1>
    <table>
        <thead>
            <tr><th>Category</th><th>Count</th></tr>
        </thead>
        <tbody>
            {''.join(f'<tr><td>{cat}</td><td>{cnt}</td></tr>' for cat, cnt in metrics.items())}
        </tbody>
    </table>
</body>
</html>\"\"\"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    logger.info("Dashboard rendering complete.")


def rebuild_dashboard(
    data_source: str = "data/raw_metrics.json",
    output_file: str = "static/dashboard.html"
) -> None:
    """
    High‑level function to rebuild the dashboard.

    It loads raw data, processes metrics, and writes the final HTML.

    Args:
        data_source: Path to the JSON file containing raw dashboard data.
        output_file: Destination path for the generated dashboard HTML.
    """
    try:
        raw = load_data(data_source)
        metrics = process_metrics(raw)
        render_dashboard(metrics, output_file)
        logger.info("Dashboard successfully rebuilt.")
    except Exception as e:
        logger.error(f"Failed to rebuild dashboard: {e}")
        raise


if __name__ == "__main__":
    # When executed directly, rebuild the dashboard using default paths.
    rebuild_dashboard()