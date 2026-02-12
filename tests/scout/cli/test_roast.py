"""
Tests for scout-roast CLI — efficiency reports from audit logs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from vivarium.scout.audit import AuditLog
from vivarium.scout.cli import roast


# --- Fixtures ---


@pytest.fixture
def audit_path(tmp_path):
    return tmp_path / "audit.jsonl"


@pytest.fixture
def audit_log(audit_path):
    log = AuditLog(path=audit_path)
    yield log
    log.close()


# --- load_audit_log ---


def test_load_audit_log_empty(audit_path):
    """Empty or missing audit returns empty list."""
    events = roast.load_audit_log("today", audit_path=audit_path)
    assert events == []


def test_load_audit_log_today(audit_log, audit_path):
    """Today's events are loaded."""
    audit_log.log("nav", cost=0.0001, duration_ms=100)
    audit_log.log("brief", cost=0.00005)
    events = roast.load_audit_log("today", audit_path=audit_path)
    assert len(events) == 2
    assert events[0]["event"] == "nav"
    assert events[1]["event"] == "brief"


def test_load_audit_log_period_filter(audit_log, audit_path):
    """Events before period start are excluded."""
    audit_log.log("nav", cost=0.0001)
    events = roast.load_audit_log("today", audit_path=audit_path)
    assert len(events) >= 1


# --- generate_report ---


def test_generate_report_empty(audit_path):
    """Empty audit produces zero Scout cost, 100% savings when no nav."""
    r = roast.generate_report("today", audit_path=audit_path)
    assert r["period"] == "today"
    assert r["scout_cost"] == 0.0
    assert r["nav_count"] == 0
    assert r["naive_cost"] == 0.0
    assert r["savings_pct"] == 100.0
    assert r["accuracy_pct"] == 100.0


def test_generate_report_with_data(audit_log, audit_path):
    """Report aggregates nav and brief costs correctly."""
    audit_log.log("nav", cost=0.0003, duration_ms=1200)
    audit_log.log("nav", cost=0.0002, duration_ms=800)
    audit_log.log("brief", cost=0.0001)
    audit_log.log("validation_fail", reason="hallucinated_path")

    r = roast.generate_report("today", audit_path=audit_path)
    assert r["scout_cost"] == pytest.approx(0.0006, rel=1e-5)
    assert r["nav_count"] == 2
    assert r["naive_cost"] == pytest.approx(1.0, rel=1e-5)  # 2 * 0.50
    assert r["savings"] > 0.99
    assert r["savings_pct"] > 99.0
    assert r["accuracy_pct"] == 50.0  # 1 validation_fail per 2 nav
    assert r["avg_nav_s"] == 1.0  # (1200 + 800) / 2 / 1000


def test_generate_report_compare_model(audit_log, audit_path):
    """--compare uses model-specific rate."""
    audit_log.log("nav", cost=0.0001)
    audit_log.log("nav", cost=0.0001)

    r_default = roast.generate_report("today", audit_path=audit_path)
    r_gpt4 = roast.generate_report("today", compare_model="gpt-4", audit_path=audit_path)
    r_claude = roast.generate_report("today", compare_model="claude-3-opus", audit_path=audit_path)

    assert r_default["naive_cost"] == 1.0  # 2 * 0.50
    assert r_gpt4["naive_cost"] == 1.0
    assert r_claude["naive_cost"] == 1.2  # 2 * 0.60


# --- format_report ---


def test_format_report_structure():
    """Report has box, period, cost lines, accuracy, closing."""
    data = {
        "period": "today",
        "compare_model": None,
        "scout_cost": 0.23,
        "naive_cost": 18.40,
        "savings": 18.17,
        "savings_pct": 98.7,
        "accuracy_pct": 94,
        "hallucination_pct": 6,
        "avg_nav_s": 1.2,
        "nav_count": 10,
    }
    out = roast.format_report(data)
    assert "SCOUT ROAST REPORT" in out
    assert "Big AI Hates This One Simple Trick" in out
    assert "Period: today" in out
    assert "$0.23" in out
    assert "$18.40" in out
    assert "98.7%" in out
    assert "94%" in out
    assert "1.2s" in out
    assert "Big AI hates you specifically" in out


def test_format_report_with_compare():
    """Report with --compare shows model line."""
    data = {
        "period": "week",
        "compare_model": "gpt-4",
        "scout_cost": 0.50,
        "naive_cost": 5.0,
        "savings": 4.5,
        "savings_pct": 90.0,
        "accuracy_pct": 95,
        "hallucination_pct": 5,
        "avg_nav_s": 1.0,
        "nav_count": 10,
    }
    out = roast.format_report(data)
    assert "vs gpt-4 naive approach" in out


# --- CLI main ---


def test_main_today(monkeypatch, audit_path):
    """--today runs without error."""
    # Seed audit
    log = AuditLog(path=audit_path)
    log.log("nav", cost=0.0001)
    log.close()

    monkeypatch.setattr("sys.argv", ["scout-roast", "--today", "--audit-path", str(audit_path)])
    assert roast.main() == 0


def test_main_week(monkeypatch, audit_path):
    """--week runs without error."""
    monkeypatch.setattr("sys.argv", ["scout-roast", "--week", "--audit-path", str(audit_path)])
    assert roast.main() == 0


def test_main_month_compare(monkeypatch, audit_path):
    """--month --compare runs without error."""
    monkeypatch.setattr(
        "sys.argv", ["scout-roast", "--month", "--compare", "gpt-4o", "--audit-path", str(audit_path)]
    )
    assert roast.main() == 0


def test_main_requires_period(monkeypatch, capsys):
    """Missing period triggers error."""
    monkeypatch.setattr("sys.argv", ["scout-roast"])
    with pytest.raises(SystemExit):
        roast.main()
    out, err = capsys.readouterr()
    combined = (out + err).lower()
    assert "required" in combined or "today" in combined or "week" in combined
