```python
#!/usr/bin/env python3
"""
generate_task_graph.py

Scans all `grind_tasks_*.json` files in the repository root,
extracts task information (id, phase, status, dependencies) and
produces an interactive HTML file with an SVG DAG visualisation.

Node colour conventions:
    - completed : green fill
    - in‑progress : transparent fill + rainbow (multicolour) stroke
    - blocked : gray fill

The resulting HTML file (task_graph.html) is written to the same
experiment directory.
"""

import json
import glob
import os
from pathlib import Path
from typing import Dict, List

import networkx as nx

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def load_tasks() -> List[Dict]:
    """
    Load all grind_tasks_*.json files from the repository root.
    Expected JSON schema (per file) – a list of task objects:
        {
            "id": "<unique-task-id>",
            "phase": "<phase-name>",
            "status": "completed" | "in_progress" | "blocked",
            "depends_on": ["<task-id>", ...]   # optional
        }
    """
    tasks = []
    for fp in glob.glob("grind_tasks_*.json"):
        with open(fp, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    tasks.extend(data)
                else:
                    # Some files may store a dict with a "tasks" key
                    tasks.extend(data.get("tasks", []))
            except json.JSONDecodeError as e:
                print(f"⚠️  Could not parse {fp}: {e}")
    return tasks


def build_graph(tasks: List[Dict]) -> nx.DiGraph:
    """Create a directed graph from task definitions."""
    G = nx.DiGraph()
    for task in tasks:
        tid = task["id"]
        G.add_node(tid, phase=task.get("phase", ""), status=task.get("status", "blocked"))
        for dep in task.get("depends_on", []):
            G.add_edge(dep, tid)  # edge from dependency -> task
    return G


def node_style(status: str) -> str:
    """Return SVG style string based on node status."""
    if status == "completed":
        return 'fill:#4caf50;stroke:#2e7d32;stroke-width:2'
    elif status == "in_progress":
        # rainbow border via stroke dash array & gradient
        return (
            'fill:none;stroke:url(#rainbow);stroke-width:3;'
        )
    else:  # blocked or unknown
        return 'fill:#9e9e9e;stroke:#616161;stroke-width:2'


def generate_svg(G: nx.DiGraph, width: int = 1200, height: int = 800) -> str:
    """Generate an SVG representation of the DAG."""
    # Layout using Graphviz (dot) for a hierarchical view
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
    except Exception:
        # Fallback to spring layout if pygraphviz is not available
        pos = nx.spring_layout(G, k=200, iterations=500)

    # Normalise positions to the desired canvas size
    xs, ys = zip(*pos.values())
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def norm(val, min_src, max_src, min_dst, max_dst):
        if max_src - min_src == 0:
            return (min_dst + max_dst) / 2
        return min_dst + (val - min_src) * (max_dst - min_dst) / (max_src - min_src)

    norm_pos = {
        n: (
            norm(x, min_x, max_x, 100, width - 100),
            norm(y, min_y, max_y, 100, height - 100),
        )
        for n, (x, y) in pos.items()
    }

    # SVG header
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        'style="font-family:Arial,Helvetica,sans-serif;">',
        # Define rainbow gradient for in‑progress borders
        '<defs>',
        '<linearGradient id="rainbow" x1="0%" y1="0%" x2="100%" y2="0%">',
        '<stop offset="0%"   stop-color="#ff0000"/>',
        '<stop offset="20%"  stop-color="#ff7f00"/>',
        '<stop offset="40%"  stop-color="#ffff00"/>',
        '<stop offset="60%"  stop-color="#00ff00"/>',
        '<stop offset="80%"  stop-color="#0000ff"/>',
        '<stop offset="100%" stop-color="#8b00ff"/>',
        '</linearGradient>',
        '</defs>',
    ]

    # Draw edges (arrows)
    for src, dst in G.edges():
        x1, y1 = norm_pos[src]
        x2, y2 = norm_pos[dst]
        # Simple straight line with arrowhead
        svg_parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="#555" stroke-width="1.5" marker-end="url(#arrow)"/>'
        )

    # Arrowhead marker definition (once)
    svg_parts.insert(
        1,
        '<defs>'
        '<marker id="arrow" markerWidth="10" markerHeight="7" refX="10" refY="3.5" '
        'orient="auto" markerUnits="strokeWidth">'
        '<polygon points="0 0, 10 3.5, 0 7" fill="#555"/>'
        '</marker>'
        '</defs>',
    )

    # Draw nodes (circles) with labels
    for node, data in G.nodes(data=True):
        x, y = norm_pos[node]
        style = node_style(data.get("status", "blocked"))
        svg_parts.append(
            f'<circle cx="{x}" cy="{y}" r="20" style="{style}" />'
        )
        # Node label (task id)
        svg_parts.append(
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" '
            f'fill="#fff" font-size="10" pointer-events="none">{node}</text>'
        )
        # Phase label (below node)
        phase = data.get("phase", "")
        if phase:
            svg_parts.append(
                f'<text x="{x}" y="{y + 35}" text-anchor="middle" '
                f'fill="#333" font-size="9">{phase}</text>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def write_html(svg_content: str, out_path: Path):
    """Wrap the SVG in a minimal HTML page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Task Dependency Graph</title>
<style>
body {{ margin:0; padding:0; display:flex; justify-content:center; align-items:center; height:100vh; background:#fafafa; }}
svg {{ background:#fff; box-shadow:0 0 10px rgba(0,0,0,0.1); }}
</style>
</head>
<body>
{svg_content}
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"✅ Graph written to {out_path}")


def main():
    tasks = load_tasks()
    if not tasks:
        print("⚠️  No tasks found – ensure grind_tasks_*.json files exist.")
        return

    G = build_graph(tasks)
    svg = generate_svg(G)
    out_file = Path(__file__).parent / "task_graph.html"
    write_html(svg, out_file)


if __name__ == "__main__":
    main()
```