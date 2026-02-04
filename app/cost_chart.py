import os
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# Paths to the data sources – adjust if your project stores them elsewhere
CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "checkpoint.json")
GRIND_LOGS_PATH = os.path.join(os.path.dirname(__file__), "grind_logs.csv")

def _load_checkpoint():
    """Load checkpoint data (expects a JSON dict with task metadata)."""
    if not os.path.exists(CHECKPOINT_PATH):
        return {}
    with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_grind_logs():
    """Load grind logs (expects CSV with columns: timestamp, task_file, phase, cost)."""
    if not os.path.exists(GRIND_LOGS_PATH):
        # Return empty DataFrame with expected columns if logs are missing
        return pd.DataFrame(columns=["timestamp", "task_file", "phase", "cost"])
    df = pd.read_csv(GRIND_LOGS_PATH)
    # Ensure timestamp is a datetime object
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def get_cost_breakdown():
    """
    Combine checkpoint and grind log data to produce a DataFrame suitable for charting.
    Returns a DataFrame with columns:
        - task_file
        - phase
        - period (YYYY-MM-DD)
        - cost
    """
    # Load data
    checkpoint = _load_checkpoint()
    logs_df = _load_grind_logs()

    # If checkpoint contains cost info per task, merge it
    if checkpoint:
        # Expect checkpoint structure: {task_id: {"task_file": "...", "phase": "...", "cost": ...}}
        cp_records = []
        for task_id, meta in checkpoint.items():
            cp_records.append({
                "timestamp": datetime.utcnow(),  # treat checkpoint as current snapshot
                "task_file": meta.get("task_file", "unknown"),
                "phase": meta.get("phase", "unknown"),
                "cost": meta.get("cost", 0.0)
            })
        cp_df = pd.DataFrame(cp_records)
        logs_df = pd.concat([logs_df, cp_df], ignore_index=True)

    if logs_df.empty:
        # Return an empty DataFrame with the expected schema
        return pd.DataFrame(columns=["task_file", "phase", "period", "cost"])

    # Derive a simple period (date) for aggregation
    logs_df["period"] = logs_df["timestamp"].dt.strftime("%Y-%m-%d")

    # Aggregate cost
    agg_df = (
        logs_df.groupby(["task_file", "phase", "period"], as_index=False)["cost"]
        .sum()
    )
    return agg_df

def render_cost_chart():
    """
    Generate a Plotly bar chart (or treemap) showing cost breakdown.
    The chart groups by task_file and phase across time periods.
    Returns a Plotly Figure object.
    """
    df = get_cost_breakdown()
    if df.empty:
        # Return a placeholder figure indicating no data
        fig = px.bar(
            x=[],
            y=[],
            title="Cost Breakdown (no data yet)",
        )
        return fig

    # Choose chart type – bar chart with facets for period
    fig = px.bar(
        df,
        x="task_file",
        y="cost",
        color="phase",
        barmode="group",
        facet_col="period",
        title="Cost Breakdown by Task File, Phase, and Day",
        labels={"cost": "Cost (USD)", "task_file": "Task File"},
        height=500,
    )
    fig.update_layout(
        legend_title_text="Phase",
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=80, b=40),
    )
    return fig
import json
from collections import defaultdict
import plotly.express as px
from datetime import datetime, timedelta

def _load_checkpoint_data():
    """
    Load the most recent checkpoint data.
    Expected format (example):
    [
        {"task_file": "foo.py", "phase": "analysis", "timestamp": "2024-02-01T12:00:00", "cost": 0.12},
        ...
    ]
    """
    try:
        with open("checkpoint.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def _load_grind_logs():
    """
    Load grind logs. Expected format (example):
    [
        {"task_file": "foo.py", "phase": "execution", "timestamp": "2024-02-01T12:05:00", "cost": 0.08},
        ...
    ]
    """
    try:
        with open("grind_logs.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def _aggregate_costs(data, period: str):
    """
    Aggregate costs by task file, phase and time period.
    period: "hour", "day", "week"
    """
    now = datetime.utcnow()
    if period == "hour":
        start = now - timedelta(hours=1)
    elif period == "day":
        start = now - timedelta(days=1)
    elif period == "week":
        start = now - timedelta(weeks=1)
    else:
        start = datetime.min

    agg = defaultdict(lambda: defaultdict(float))

    for entry in data:
        ts = datetime.fromisoformat(entry["timestamp"])
        if ts < start:
            continue
        key = (entry["task_file"], entry["phase"])
        agg[key][period] += entry["cost"]
    return agg

def get_cost_breakdown_chart(period: str = "day"):
    """
    Return a Plotly bar‑chart (HTML) showing cost broken down by
    task file and phase for the given time period.
    """
    checkpoint = _load_checkpoint_data()
    grind = _load_grind_logs()
    combined = checkpoint + grind

    agg = _aggregate_costs(combined, period)

    # Prepare data for Plotly
    rows = []
    for (task_file, phase), costs in agg.items():
        rows.append({
            "Task File": task_file,
            "Phase": phase,
            "Cost": costs[period]
        })

    if not rows:
        return "<p>No cost data available for the selected period.</p>"

    fig = px.bar(
        rows,
        x="Task File",
        y="Cost",
        color="Phase",
        title=f"Cost Breakdown – Last {period.capitalize()}",
        labels={"Cost": "Cost (USD)"},
        barmode="stack",
        height=400,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig.to_html(full_html=False, include_plotlyjs="cdn")
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import io
import base64

def load_checkpoint_data(checkpoint_path):
    """Load checkpoint JSON data."""
    with open(checkpoint_path, 'r') as f:
        return json.load(f)

def load_grind_logs(log_path):
    """Load grind logs JSON data."""
    with open(log_path, 'r') as f:
        return json.load(f)

def aggregate_costs(checkpoint_data, grind_logs):
    """
    Aggregate costs by task file, phase, and time period.
    Returns a dict of the form:
    {
        (task_file, phase, period): total_cost,
        ...
    }
    """
    costs = defaultdict(float)

    # Example structure assumptions:
    # checkpoint_data = {"tasks": [{"file": "foo.py", "phase": "analysis", "cost": 0.5, "timestamp": 1698000000}, ...]}
    # grind_logs = {"entries": [{"file": "foo.py", "phase": "execution", "cost": 1.2, "timestamp": 1698003600}, ...]}

    for entry in checkpoint_data.get("tasks", []):
        period = _period_from_timestamp(entry.get("timestamp"))
        key = (entry.get("file"), entry.get("phase"), period)
        costs[key] += entry.get("cost", 0)

    for entry in grind_logs.get("entries", []):
        period = _period_from_timestamp(entry.get("timestamp"))
        key = (entry.get("file"), entry.get("phase"), period)
        costs[key] += entry.get("cost", 0)

    return costs

def _period_from_timestamp(ts):
    """Convert a Unix timestamp to a simple period string (e.g., '2023-10-01')."""
    from datetime import datetime
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')

def build_bar_chart(costs):
    """
    Build a simple stacked bar chart: X‑axis = time period,
    each bar stacked by phase, colored per task file.
    Returns a base64‑encoded PNG image.
    """
    # Organise data
    periods = sorted({period for (_, _, period) in costs})
    phases = sorted({phase for (_, phase, _) in costs})
    files = sorted({file for (file, _, _) in costs})

    # Prepare a mapping: (period, phase, file) -> cost
    data = defaultdict(lambda: defaultdict(float))
    for (file, phase, period), cost in costs.items():
        data[(period, phase)][file] += cost

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = [0] * len(periods)

    # Color map for files
    cmap = plt.get_cmap('tab20')
    file_colors = {file: cmap(i % 20) for i, file in enumerate(files)}

    for phase in phases:
        heights = []
        for i, period in enumerate(periods):
            period_phase_key = (period, phase)
            total = sum(data[period_phase_key].values())
            heights.append(total)
        ax.bar(periods, heights, bottom=bottom, label=phase)
        # Update bottom for stacking
        bottom = [b + h for b, h in zip(bottom, heights)]

    ax.set_xlabel('Time Period')
    ax.set_ylabel('Cost')
    ax.set_title('Cost Breakdown by Phase Over Time')
    ax.legend(title='Phase')
    plt.xticks(rotation=45)

    # Encode to base64
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

def get_cost_chart_image(checkpoint_path, grind_log_path):
    """
    Public helper to be called from the UI layer.
    Returns a base64 PNG image of the cost breakdown chart.
    """
    checkpoint_data = load_checkpoint_data(checkpoint_path)
    grind_logs = load_grind_logs(grind_log_path)
    costs = aggregate_costs(checkpoint_data, grind_logs)
    return build_bar_chart(costs)
import os
import json
from datetime import datetime
from collections import defaultdict

import pandas as pd
import plotly.express as px

# Paths to the data sources – adjust if your project stores them elsewhere
CHECKPOINT_DIR = os.path.join(os.path.dirname(__file__), "checkpoint")
GRIND_LOGS_DIR = os.path.join(os.path.dirname(__file__), "grind_logs")

def _load_json_files(directory):
    """Yield JSON objects from all .json files in a directory."""
    for filename in os.listdir(directory):
        if not filename.lower().endswith(".json"):
            continue
        full_path = os.path.join(directory, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                yield json.load(f)
        except Exception:
            # Silently skip malformed files – they shouldn't stop the chart
            continue

def _aggregate_costs():
    """
    Build a DataFrame with columns:
        - task_file
        - phase
        - timestamp (datetime)
        - cost (float)
    The function merges data from checkpoint and grind_logs.
    """
    records = []

    # Load checkpoint data
    for entry in _load_json_files(CHECKPOINT_DIR):
        # Expected keys: "task_file", "phase", "timestamp", "cost"
        try:
            records.append({
                "task_file": entry.get("task_file", "unknown"),
                "phase": entry.get("phase", "unknown"),
                "timestamp": datetime.fromisoformat(entry["timestamp"]),
                "cost": float(entry.get("cost", 0)),
            })
        except Exception:
            continue

    # Load grind log data (may have a slightly different schema)
    for entry in _load_json_files(GRIND_LOGS_DIR):
        try:
            records.append({
                "task_file": entry.get("task_file", "unknown"),
                "phase": entry.get("phase", "unknown"),
                "timestamp": datetime.fromisoformat(entry["timestamp"]),
                "cost": float(entry.get("cost", 0)),
            })
        except Exception:
            continue

    df = pd.DataFrame(records)
    if df.empty:
        # Return an empty DataFrame with the expected columns to avoid downstream errors
        df = pd.DataFrame(columns=["task_file", "phase", "timestamp", "cost"])
    return df

def get_cost_breakdown_chart(time_bucket="D"):
    """
    Return a Plotly figure showing cost breakdown by task file, phase, and time period.

    Parameters
    ----------
    time_bucket : str, optional
        Pandas offset alias for grouping time periods.
        "D" = day, "W" = week, "M" = month, etc. Default is daily.

    Returns
    -------
    plotly.graph_objects.Figure
        A treemap where the hierarchy is: Time Period → Phase → Task File.
        The size of each rectangle corresponds to the total cost.
    """
    df = _aggregate_costs()
    if df.empty:
        # Return a minimal placeholder figure
        return px.bar(title="No cost data available yet")

    # Create a time bucket column
    df["time_period"] = df["timestamp"].dt.to_period(time_bucket).astype(str)

    # Aggregate cost
    agg = (
        df.groupby(["time_period", "phase", "task_file"], as_index=False)["cost"]
        .sum()
    )

    # Build a treemap
    fig = px.treemap(
        agg,
        path=["time_period", "phase", "task_file"],
        values="cost",
        title="Cost Breakdown (by Time Period → Phase → Task File)",
        color="cost",
        color_continuous_scale="Blues",
    )
    fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))
    return fig