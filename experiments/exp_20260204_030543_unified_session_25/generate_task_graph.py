#!/usr/bin/env python3
"""
generate_task_graph.py

Parse all `grind_tasks_*.json` files in the workspace, extract task phases,
dependencies and status, then render a directed acyclic graph (DAG) as an SVG.

Node styling:
  * completed   → green fill
  * in‑progress → transparent fill with a rainbow (multicolour) border
  * blocked     → gray fill

The resulting SVG is written to `task_graph.svg` in the same directory.
"""

import json
import pathlib
import sys
from collections import defaultdict

# Try to import graphviz – if unavailable, give a clear error.
try:
    from graphviz import Digraph
except ImportError as exc:
    sys.stderr.write(
        "Error: The 'graphviz' Python package is required. Install it with:\n"
        "    pip install graphviz\n"
    )
    raise exc

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

# Workspace root (where the grind_tasks_*.json files live)
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]  # /app

# Output directory (experiment folder)
OUTPUT_DIR = pathlib.Path(__file__).parent
OUTPUT_SVG = OUTPUT_DIR / "task_graph.svg"

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def load_task_files():
    """Yield (filepath, parsed_json) for each grind_tasks_*.json file."""
    pattern = "grind_tasks_*.json"
    for p in WORKSPACE_ROOT.glob(pattern):
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                yield p, data
        except Exception as e:
            sys.stderr.write(f"Warning: Could not parse {p}: {e}\n")

def extract_tasks():
    """
    Build dictionaries:
      tasks[task_id] = {"phase": ..., "status": ..., "deps": [...]}
    """
    tasks = {}
    for path, data in load_task_files():
        # The JSON format is not strictly defined; we support two common shapes:
        # 1. A list of task objects.
        # 2. A dict mapping task IDs to objects.
        if isinstance(data, list):
            iterable = data
        elif isinstance(data, dict):
            iterable = data.values()
        else:
            sys.stderr.write(f"Skipping unsupported JSON structure in {path}\n")
            continue

        for entry in iterable:
            # Expected keys (fallback defaults if missing)
            task_id = entry.get("id") or entry.get("name")
            if not task_id:
                continue
            phase = entry.get("phase", "unknown")
            status = entry.get("status", "blocked").lower()
            deps = entry.get("dependencies", [])
            # Ensure deps is a list of ids
            if isinstance(deps, str):
                deps = [deps]
            elif not isinstance(deps, list):
                deps = list(deps)

            tasks[task_id] = {
                "phase": phase,
                "status": status,
                "deps": deps,
            }
    return tasks

def style_for_status(status):
    """Return (fillcolor, style, penwidth, color) for a given task status."""
    status = status.lower()
    if status == "completed":
        return ("#8fbc8f", "filled", "1", "#000000")  # green fill
    elif status in ("in-progress", "in_progress", "running"):
        # Transparent fill, rainbow border (approximate with gradient via HTML-like label)
        # Graphviz does not support gradient borders directly, so we emulate with a thick multicolour pen.
        return ("transparent", "filled", "3", "rainbow")
    else:  # blocked or unknown
        return ("#d3d3d3", "filled", "1", "#000000")  # gray fill

def add_rainbow_border(node_attrs):
    """
    Graphviz cannot directly set a rainbow border, but we can cheat by using
    a HTML-like label with a <TABLE> that has a coloured background and a
    transparent inner cell. This gives a colourful outline effect.
    """
    rainbow = (
        "#ff0000", "#ff7f00", "#ffff00", "#00ff00",
        "#0000ff", "#4b0082", "#8b00ff"
    )
    # Create a thin table with coloured cells around a transparent center.
    rows = []
    for color in rainbow:
        rows.append(
            f'<TR><TD BGCOLOR="{color}" WIDTH="100%" HEIGHT="2"></TD></TR>'
        )
    inner = '<TR><TD BGCOLOR="transparent" WIDTH="100%" HEIGHT="16"></TD></TR>'
    table = f"""<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0">
{''.join(rows)}
{inner}
{''.join(reversed(rows))}
</TABLE>>"""
    node_attrs["label"] = table
    node_attrs["shape"] = "plaintext"
    return node_attrs

def build_graph(tasks):
    dot = Digraph(comment="Task Dependency Graph", format="svg")
    dot.attr(rankdir="LR", splines="ortho")
    # Add nodes
    for task_id, info in tasks.items():
        fill, style, penwidth, border = style_for_status(info["status"])
        attrs = {
            "style": style,
            "fillcolor": fill,
            "penwidth": penwidth,
            "color": border,
            "shape": "box",
            "fontname": "Helvetica",
            "fontsize": "10",
        }
        if border == "rainbow":
            attrs = add_rainbow_border(attrs)
        # Include phase in label for readability
        label = f"{task_id}\\n({info['phase']})"
        attrs["label"] = label
        dot.node(task_id, **attrs)

    # Add edges (dependencies)
    for task_id, info in tasks.items():
        for dep in info["deps"]:
            if dep in tasks:
                dot.edge(dep, task_id)
            else:
                # dangling dependency – still render as a node with gray style
                dot.node(dep, style="filled", fillcolor="#d3d3d3", shape="box")
                dot.edge(dep, task_id)

    return dot

def main():
    tasks = extract_tasks()
    if not tasks:
        sys.stderr.write("No tasks found – aborting.\n")
        sys.exit(1)

    dot = build_graph(tasks)

    # Render to SVG
    try:
        dot.render(filename=str(OUTPUT_SVG.with_suffix("")), cleanup=True)
        print(f"Task graph generated: {OUTPUT_SVG}")
    except Exception as e:
        sys.stderr.write(f"Failed to render SVG: {e}\n")
        sys.exit(2)

if __name__ == "__main__":
    main()