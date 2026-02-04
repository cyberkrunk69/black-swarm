#!/usr/bin/env python3
"""
generate_task_graph.py

Scans all `grind_tasks_*.json` files in the workspace, extracts task information,
builds a directed acyclic graph (DAG) of task dependencies, and renders the graph
as an SVG file (`task_graph.svg`) using NetworkX + Matplotlib.

Node coloring:
  - Completed:   green
  - In‑progress: orange fill with a rainbow (multi‑color) border
  - Blocked:     gray

Usage:
    python generate_task_graph.py
"""

import json
import pathlib
import sys

# --- Optional imports ---------------------------------------------------------
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
except ImportError as e:
    sys.stderr.write(
        "Required libraries missing. Install with:\n"
        "    pip install networkx matplotlib\n"
    )
    raise e

# -----------------------------------------------------------------------------


def load_tasks():
    """
    Load all grind_tasks_*.json files from the repository root.
    Expected JSON schema (per task entry):
        {
            "id": "<unique_task_id>",
            "phase": "<phase_name>",
            "dependencies": ["<task_id>", ...],
            "status": "completed" | "in_progress" | "blocked"
        }
    Returns:
        dict mapping task_id -> task_dict
    """
    workspace = pathlib.Path(__file__).resolve().parents[2]  # /app
    task_files = list(workspace.glob("grind_tasks_*.json"))
    if not task_files:
        sys.stderr.write("No grind_tasks_*.json files found in workspace.\n")
        sys.exit(1)

    tasks = {}
    for f in task_files:
        try:
            with f.open() as fp:
                data = json.load(fp)
                for entry in data:
                    tid = entry["id"]
                    tasks[tid] = entry
        except Exception as exc:
            sys.stderr.write(f"Failed to parse {f}: {exc}\n")
            continue
    return tasks


def build_graph(tasks):
    """
    Build a directed graph from the task dictionary.
    """
    G = nx.DiGraph()
    for tid, info in tasks.items():
        G.add_node(tid, **info)
        for dep in info.get("dependencies", []):
            if dep in tasks:
                G.add_edge(dep, tid)
            else:
                # Add a placeholder node for missing dependencies
                G.add_node(dep, phase="unknown", status="blocked")
                G.add_edge(dep, tid)
    return G


def draw_graph(G, output_path):
    """
    Render the DAG to an SVG file.
    """
    plt.figure(figsize=(12, 8))
    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Determine node colors and edge styles based on status
    node_colors = []
    node_edgecolors = []
    node_linewidths = []

    for node in G.nodes:
        status = G.nodes[node].get("status", "blocked")
        if status == "completed":
            node_colors.append("#8fbc8f")          # greenish
            node_edgecolors.append("#2e8b57")
            node_linewidths.append(1.0)
        elif status == "in_progress":
            node_colors.append("#ffa500")          # orange fill
            node_edgecolors.append("#ff00ff")      # rainbow-esque (magenta)
            node_linewidths.append(3.0)
        else:  # blocked or unknown
            node_colors.append("#d3d3d3")          # light gray
            node_edgecolors.append("#808080")
            node_linewidths.append(1.0)

    # Draw nodes
    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        edgecolors=node_edgecolors,
        linewidths=node_linewidths,
        node_size=1500,
        node_shape="s",
    )

    # Draw edges
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>", arrowsize=12)

    # Labels: show task id + phase (optional)
    labels = {
        n: f"{n}\n{G.nodes[n].get('phase','')}"
        for n in G.nodes
    }
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_family="sans-serif")

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, format="svg")
    plt.close()


def main():
    tasks = load_tasks()
    graph = build_graph(tasks)
    out_file = pathlib.Path(__file__).with_name("task_graph.svg")
    draw_graph(graph, out_file)
    print(f"Task dependency graph written to {out_file}")


if __name__ == "__main__":
    main()