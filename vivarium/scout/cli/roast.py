"""
Scout Roast CLI — Efficiency reports from audit logs.

"Big AI hates this one simple trick." Generate savings reports that make
expensive tool usage tangible and shame-heavy.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from vivarium.scout.audit import AuditLog, DEFAULT_AUDIT_PATH

# Period type identifier
PERIOD_TODAY = "today"
PERIOD_WEEK = "week"
PERIOD_MONTH = "month"

# Estimated cost per "naive" navigation (no Scout) — $/nav, typical 25k tokens at premium rates
# Prompt: "Assume 10x tokens for exploration, $3/million (GPT-4 rate)" → ~$0.50/nav conservative
DEFAULT_NAIVE_COST_PER_NAV = 0.50

# Model-specific rates for --compare (cost per naive nav in USD)
MODEL_RATES: Dict[str, float] = {
    "gpt-4": 0.50,
    "gpt-4-turbo": 0.50,
    "gpt-4o": 0.25,
    "gpt-4o-mini": 0.10,
    "claude-3-opus": 0.60,
    "claude-3-sonnet": 0.25,
    "claude-3-haiku": 0.05,
}


def _parse_archive_timestamp(name: str) -> Optional[datetime]:
    """Parse audit_YYYYMMDD_HHMMSS.jsonl.gz → datetime in UTC."""
    m = re.match(r"audit_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})\.jsonl\.gz", name)
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), int(m.group(6)),
            tzinfo=timezone.utc,
        )
    except (ValueError, TypeError):
        return None


def _iter_archive_lines(path: Path) -> List[str]:
    """Yield non-empty lines from a gzipped JSONL archive."""
    lines: List[str] = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if line:
                    lines.append(line)
    except (OSError, gzip.BadGzipFile) as e:
        sys.stderr.write(f"scout-roast: warn: skip archive {path}: {e}\n")
    return lines


def load_audit_log(
    period: str,
    audit_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Load audit events for the given period from current + archived logs.

    Args:
        period: "today" | "week" | "month"
        audit_path: Override audit log path (default: ~/.scout/audit.jsonl)

    Returns:
        Sorted list of events with ts >= since.
    """
    path = Path(audit_path).expanduser().resolve() if audit_path else DEFAULT_AUDIT_PATH
    now = datetime.now(timezone.utc)

    if period == PERIOD_TODAY:
        since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == PERIOD_WEEK:
        since = now - timedelta(days=7)
    elif period == PERIOD_MONTH:
        since = now - timedelta(days=30)
    else:
        since = now - timedelta(days=1)  # fallback

    since_ts = since.isoformat()
    events: List[Dict[str, Any]] = []

    # 1. Current audit.jsonl
    if path.exists():
        log = AuditLog(path=path)
        try:
            for e in log.query(since=since):
                events.append(e)
        finally:
            log.close()

    # 2. Archived logs (audit_YYYYMMDD_HHMMSS.jsonl.gz)
    parent = path.parent
    if parent.exists():
        for f in parent.glob("audit_*.jsonl.gz"):
            ts = _parse_archive_timestamp(f.name)
            if ts is None or ts <= since:
                continue
            for line in _iter_archive_lines(f):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("ts", "") >= since_ts:
                    events.append(obj)

    events.sort(key=lambda e: e.get("ts", ""))
    return events


def calculate_accuracy(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute accuracy metrics: total_nav, validation_fail_count, accuracy_pct."""
    nav_events = [e for e in events if e.get("event") == "nav"]
    validation_fails = [e for e in events if e.get("event") == "validation_fail"]
    total_nav = len(nav_events)
    fail_count = len(validation_fails)
    if total_nav == 0:
        return {
            "total_nav": 0,
            "validation_fail_count": fail_count,
            "accuracy_pct": 100.0,
        }
    accuracy = 100.0 * (total_nav - fail_count) / total_nav
    return {
        "total_nav": total_nav,
        "validation_fail_count": fail_count,
        "accuracy_pct": round(accuracy, 2),
    }


def generate_report(
    period: str,
    compare_model: Optional[str] = None,
    audit_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Generate roast report from audit events.

    Returns dict with scout_cost, naive_cost, savings, savings_pct, accuracy, avg_nav_s.
    """
    events = load_audit_log(period, audit_path)

    scout_cost = sum(
        e.get("cost") or 0
        for e in events
        if e.get("event") in ("nav", "brief")
    )
    nav_events = [e for e in events if e.get("event") == "nav"]
    nav_count = len(nav_events)

    cost_per_nav = DEFAULT_NAIVE_COST_PER_NAV
    if compare_model:
        cost_per_nav = MODEL_RATES.get(
            compare_model.lower(),
            DEFAULT_NAIVE_COST_PER_NAV,
        )

    naive_cost = nav_count * cost_per_nav
    savings = max(0.0, naive_cost - scout_cost)
    savings_pct = (100.0 * savings / naive_cost) if naive_cost > 0 else 100.0

    accuracy_data = calculate_accuracy(events)
    accuracy_pct = accuracy_data["accuracy_pct"]

    nav_durations = [
        e.get("duration_ms")
        for e in nav_events
        if e.get("duration_ms") is not None
    ]
    avg_nav_s = (sum(nav_durations) / len(nav_durations) / 1000.0) if nav_durations else 0.0

    return {
        "period": period,
        "compare_model": compare_model,
        "scout_cost": scout_cost,
        "naive_cost": naive_cost,
        "savings": savings,
        "savings_pct": round(savings_pct, 1),
        "accuracy_pct": accuracy_pct,
        "hallucination_pct": round(100.0 - accuracy_pct, 1),
        "avg_nav_s": round(avg_nav_s, 1),
        "nav_count": nav_count,
    }


def format_report(data: Dict[str, Any]) -> str:
    """Format roast report as ASCII box."""
    width = 62
    lines = [
        "╔" + "═" * width + "╗",
        "║" + "           🔥 SCOUT ROAST REPORT 🔥                           ".ljust(width) + "║",
        "║" + "           \"Big AI Hates This One Simple Trick\"               ".ljust(width) + "║",
        "╠" + "═" * width + "╣",
        "  Period: " + data["period"],
        "",
        f"  💰 Scout Spent:        ${data['scout_cost']:.2f}",
        f"  💸 Expensive Model Avoided: ${data['naive_cost']:.2f}",
        f"  📊 Savings:            {data['savings_pct']:.1f}%",
        "",
        f"  🎯 Accuracy:           {data['accuracy_pct']:.0f}% ({data['hallucination_pct']:.0f}% hallucination, recovered)",
        f"  ⚡ Avg Navigation:     {data['avg_nav_s']:.1f}s",
        "",
    ]

    compare = data.get("compare_model")
    if compare:
        lines.append(f'  (vs {compare} naive approach)')
        lines.append("")
    else:
        lines.append('  "Big AI hates you specifically"')
        lines.append("")

    lines.append("╚" + "═" * width + "╝")
    return "\n".join(lines)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="scout-roast",
        description="Scout Roast — efficiency reports from audit logs. Show the money you didn't spend.",
    )
    period_group = parser.add_mutually_exclusive_group(required=True)
    period_group.add_argument("--today", action="store_const", dest="period", const=PERIOD_TODAY)
    period_group.add_argument("--week", action="store_const", dest="period", const=PERIOD_WEEK)
    period_group.add_argument("--month", action="store_const", dest="period", const=PERIOD_MONTH)
    parser.add_argument(
        "--compare",
        metavar="MODEL",
        help="Compare vs specific model (e.g. gpt-4, gpt-4o, claude-3-opus)",
    )
    parser.add_argument(
        "--audit-path",
        metavar="PATH",
        type=Path,
        help="Override audit log path (default: ~/.scout/audit.jsonl)",
    )
    args = parser.parse_args()

    if args.period is None:
        parser.error("One of --today, --week, --month is required")

    report = generate_report(
        period=args.period,
        compare_model=args.compare,
        audit_path=args.audit_path,
    )
    print(format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
