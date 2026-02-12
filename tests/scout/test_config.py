"""Tests for ScoutConfig — layered loading, hard caps, trigger resolution."""

import os
from pathlib import Path

import pytest

from vivarium.scout.config import (
    DEFAULT_CONFIG,
    HARD_MAX_COST_PER_EVENT,
    HARD_MAX_HOURLY_BUDGET,
    ScoutConfig,
    TriggerConfig,
)


def _write_yaml(path: Path, data: dict) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def test_precedence_env_over_yaml(tmp_path: Path, monkeypatch):
    """Env vars override YAML."""
    user_config = tmp_path / "user_scout" / "config.yaml"
    user_config.parent.mkdir(parents=True)
    _write_yaml(user_config, {"limits": {"max_cost_per_event": 0.03}})

    monkeypatch.setenv("SCOUT_MAX_COST_PER_EVENT", "0.07")
    config = ScoutConfig(search_paths=[user_config])
    assert config.get("limits")["max_cost_per_event"] == 0.07


def test_precedence_project_over_user(tmp_path: Path):
    """Project config overrides user config."""
    user_dir = tmp_path / "home" / ".scout"
    user_dir.mkdir(parents=True)
    user_config = user_dir / "config.yaml"
    _write_yaml(user_config, {"limits": {"max_cost_per_event": 0.02}})

    proj_dir = tmp_path / "proj" / ".scout"
    proj_dir.mkdir(parents=True)
    proj_config = proj_dir / "config.yaml"
    _write_yaml(proj_config, {"limits": {"max_cost_per_event": 0.04}})

    config = ScoutConfig(search_paths=[user_config, proj_config])
    assert config.get("limits")["max_cost_per_event"] == 0.04


def test_hard_cap_enforcement(tmp_path: Path, monkeypatch):
    """User cannot exceed hard safety caps."""
    monkeypatch.setenv("SCOUT_MAX_COST_PER_EVENT", "999.00")
    monkeypatch.setenv("SCOUT_HOURLY_BUDGET", "999.00")
    config = ScoutConfig(search_paths=[])

    assert config.effective_max_cost() <= HARD_MAX_COST_PER_EVENT
    assert config._raw["limits"]["hourly_budget"] == 999.0
    # should_process still enforces hard cap
    assert config.should_process(50.0, hourly_spend=0) is False
    assert config.should_process(0.5, hourly_spend=0) is True
    assert config.should_process(0.5, hourly_spend=15.0) is False  # over hourly cap


def test_trigger_pattern_matching(tmp_path: Path):
    """First pattern match wins; glob patterns work."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg_path = config_dir / "config.yaml"
    _write_yaml(
        cfg_path,
        {
            "triggers": {
                "default": "manual",
                "patterns": [
                    {"pattern": "vivarium/runtime/*.py", "trigger": "on-save", "max_cost": 0.02},
                    {"pattern": "tests/*", "trigger": "manual"},
                    {"pattern": "tests/*/*", "trigger": "manual"},
                    {"pattern": "docs/*.md", "trigger": "disabled"},
                ],
            },
        },
    )
    config = ScoutConfig(search_paths=[cfg_path])

    # Pattern 1: vivarium/runtime
    t1 = config.resolve_trigger(Path("vivarium/runtime/foo.py"))
    assert t1.type == "on-save"
    assert t1.max_cost == 0.02

    # Pattern 2: tests (single level)
    t2a = config.resolve_trigger(Path("tests/test_foo.py"))
    assert t2a.type == "manual"
    # Pattern 2: tests (nested)
    t2b = config.resolve_trigger(Path("tests/unit/test_foo.py"))
    assert t2b.type == "manual"

    # Pattern 3: docs
    t3 = config.resolve_trigger(Path("docs/README.md"))
    assert t3.type == "disabled"

    # Default for non-matching
    t4 = config.resolve_trigger(Path("scripts/foo.sh"))
    assert t4.type == "manual"
    assert t4.max_cost <= HARD_MAX_COST_PER_EVENT


def test_effective_max_cost_per_file(tmp_path: Path):
    """effective_max_cost respects pattern-specific max_cost."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg_path = config_dir / "config.yaml"
    _write_yaml(
        cfg_path,
        {
            "triggers": {
                "default": "on-commit",
                "patterns": [
                    {"pattern": "vivarium/*.py", "trigger": "on-save", "max_cost": 0.01},
                ],
            },
            "limits": {"max_cost_per_event": 0.10},
        },
    )
    config = ScoutConfig(search_paths=[cfg_path])

    assert config.effective_max_cost(Path("vivarium/foo.py")) == 0.01
    assert config.effective_max_cost(Path("other/foo.py")) == 0.10


def test_should_process(tmp_path: Path):
    """should_process checks per-event and hourly limits."""
    # Use explicit config to avoid loading from ~/.scout
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg_path = config_dir / "config.yaml"
    _write_yaml(cfg_path, {"limits": {"max_cost_per_event": 0.10, "hourly_budget": 1.0}})
    config = ScoutConfig(search_paths=[cfg_path])

    assert config.should_process(0.01, hourly_spend=0) is True
    assert config.should_process(0.05, hourly_spend=0) is True
    # 0.05 + 0.95 = 1.00, hourly_budget is 1.0 -> at limit, still ok
    assert config.should_process(0.05, hourly_spend=0.95) is True
    # 0.10 + 0.95 = 1.05 > 1.0 -> over hourly budget
    assert config.should_process(0.10, hourly_spend=0.95) is False
    assert config.should_process(2.0, hourly_spend=0) is False


def test_invalid_yaml_handling(tmp_path: Path):
    """Invalid YAML is skipped with warning, defaults used."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("triggers:\n  default: [unclosed\n")

    config = ScoutConfig(search_paths=[bad_yaml])
    # Should not crash; should fall back to defaults
    assert config.get("triggers")["default"] == "on-commit"


def test_validate_yaml(tmp_path: Path):
    """validate_yaml checks syntax."""
    config = ScoutConfig(search_paths=[])

    ok, msg = config.validate_yaml()
    assert ok is True

    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text("invalid: [")
    ok, msg = config.validate_yaml(bad_path)
    assert ok is False
    assert len(msg) > 0


def test_to_dict():
    """to_dict returns effective config for audit."""
    config = ScoutConfig(search_paths=[])
    d = config.to_dict()
    assert "triggers" in d
    assert "limits" in d
    assert "models" in d
    assert "notifications" in d
    assert "hard_caps" in d
    assert d["hard_caps"]["max_cost_per_event"] == HARD_MAX_COST_PER_EVENT
    assert d["hard_caps"]["hourly_budget"] == HARD_MAX_HOURLY_BUDGET


def test_get_set(tmp_path: Path, monkeypatch):
    """get/set work with dot paths."""
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".scout"
    config_dir.mkdir()
    cfg_path = config_dir / "config.yaml"
    _write_yaml(cfg_path, DEFAULT_CONFIG)

    config = ScoutConfig(search_paths=[cfg_path])
    assert config.get("triggers.default") == "on-commit"

    # set writes to file (project config exists at tmp_path/.scout/config.yaml)
    success = config.set("limits.hourly_budget", 2.0)
    assert success is True
    assert config.get("limits.hourly_budget") == 2.0


def test_path_matching_fnmatch_style(tmp_path: Path):
    """Glob patterns match correctly (fnmatch-style)."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg_path = config_dir / "config.yaml"
    _write_yaml(
        cfg_path,
        {
            "triggers": {
                "default": "manual",
                "patterns": [
                    {"pattern": "*.py", "trigger": "on-save"},
                ],
            },
        },
    )
    config = ScoutConfig(search_paths=[cfg_path])

    t = config.resolve_trigger(Path("foo.py"))
    assert t.type == "on-save"


def test_tui_flow(monkeypatch):
    """TUI returns False when questionary not installed."""
    # When questionary is not installed, run_config_tui returns False
    try:
        import questionary  # noqa: F401
        has_q = True
    except ImportError:
        has_q = False

    if not has_q:
        from vivarium.scout.tui import run_config_tui
        assert run_config_tui() is False
    else:
        # When installed, mock select to return cancel immediately
        from unittest.mock import MagicMock
        mock_select = MagicMock()
        mock_select.return_value.ask.return_value = "cancel"
        monkeypatch.setattr("vivarium.scout.tui.questionary.select", mock_select)
        from vivarium.scout.tui import run_config_tui
        assert run_config_tui() is False
