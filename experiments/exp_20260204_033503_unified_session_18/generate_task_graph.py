#!/usr/bin/env python3
"""
generate_task_graph.py

Scans all `grind_tasks_*.json` files in the workspace, extracts the
`phase`, `status`, and `dependencies` fields, builds a directed acyclic
graph (DAG) and outputs a self‑contained HTML file (`task_graph.html`)
that visualises the graph with SVG.

Node colour conventions:
    - completed   → green
    - in‑progress → rainbow border (gradient)
    - blocked     → gray
"""

import json
import glob
import os
from pathlib import Path
from typing import Dict, List

try:
    from graphviz import Digraph
except ImportError as e:
    raise RuntimeError(
        "The 'graphviz' Python package is required. Install it with "
        "`pip install graphviz` and ensure the Graphviz system binaries are available."
    ) from e


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def load_tasks() -> List[Dict]:
    """Load all grind_tasks_*.json files from the workspace root."""
    task_files = glob.glob("grind_tasks_*.json")
    tasks = []
    for tf in task_files:
        with open(tf, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Expect each file to contain a list of task objects or a single dict
            if isinstance(data, list):
                tasks.extend(data)
            else:
                tasks.append(data)
    return tasks


def build_graph(tasks: List[Dict]) -> Digraph:
    """Create a Graphviz Digraph from task data."""
    dot = Digraph(comment="Task Dependency Graph", format="svg")
    dot.attr(rankdir="LR", splines="ortho", nodesep="0.5", ranksep="1")

    # Define node style based on status
    for task in tasks:
        task_id = str(task.get("id", task.get("name")))
        phase = task.get("phase", "unknown")
        status = task.get("status", "blocked").lower()

        # Base node attributes
        attrs = {
            "label": f"{task_id}\\n{phase}",
            "shape": "box",
            "style": "filled",
            "fillcolor": "white",
        }

        # Colour / border handling
        if status == "completed":
            attrs["fillcolor"] = "#8BC34A"  # green
            attrs["fontcolor"] = "black"
        elif status in ("in-progress", "in_progress", "running"):
            # Rainbow border via HTML-like label
            attrs["fillcolor"] = "white"
            attrs["color"] = "url(#rainbowGradient)"
            attrs["penwidth"] = "3"
        else:  # blocked or unknown
            attrs["fillcolor"] = "#B0BEC5"  # gray
            attrs["fontcolor"] = "black"

        dot.node(task_id, **attrs)

    # Add edges for dependencies
    for task in tasks:
        task_id = str(task.get("id", task.get("name")))
        deps = task.get("dependencies", [])
        for dep in deps:
            dep_id = str(dep)
            dot.edge(dep_id, task_id)

    # Define a rainbow gradient for the border (used only when needed)
    dot.body.append(
        """\
<defs>
  <linearGradient id="rainbowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%"   stop-color="#ff0000"/>
    <stop offset="20%"  stop-color="#ff7f00"/>
    <stop offset="40%"  stop-color="#ffff00"/>
    <stop offset="60%"  stop-color="#00ff00"/>
    <stop offset="80%"  stop-color="#0000ff"/>
    <stop offset="100%" stop-color="#8b00ff"/>
  </linearGradient>
</defs>
"""
    )
    return dot


def write_html(svg_content: str, output_path: Path):
    """Wrap the raw SVG in a minimal HTML page."""
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Task Dependency Graph</title>
<style>
  body {{ margin: 0; padding: 0; font-family: Arial, sans-serif; }}
  .graph-container {{ width: 100vw; height: 100vh; overflow: auto; }}
</style>
</head>
<body>
<div class="graph-container">
{svg_content}
</div>
</body>
</html>
"""
    output_path.write_text(html_template, encoding="utf-8")
    print(f"✅ Graph HTML written to {output_path}")


def main():
    tasks = load_tasks()
    if not tasks:
        print("⚠️ No grind_tasks_*.json files found in the workspace.")
        return

    dot = build_graph(tasks)

    # Render SVG as a string (no file on disk)
    svg_bytes = dot.pipe()
    svg_str = svg_bytes.decode("utf-8")

    # Output HTML file next to this script
    out_file = Path(__file__).parent / "task_graph.html"
    write_html(svg_str, out_file)


if __name__ == "__main__":
    main()