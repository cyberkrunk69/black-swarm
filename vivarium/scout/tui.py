"""
Scout Configuration TUI — Interactive terminal UI for editing config.

Uses questionary for prompts and rich for display.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from vivarium.scout.config import (
    DEFAULT_CONFIG,
    HARD_MAX_HOURLY_BUDGET,
    ScoutConfig,
)


def _render_header() -> str:
    """Return header text for the TUI."""
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console()
        with console.capture() as capture:
            console.print(
                Panel(
                    "[bold]Scout Configuration[/bold]",
                    style="dim",
                    border_style="cyan",
                )
            )
        return capture.get()
    except ImportError:
        return "═══════════════════════════════════════════════════\nScout Configuration\n═══════════════════════════════════════════════════\n"


def run_config_tui() -> bool:
    """
    Run interactive config TUI. Returns True if config was saved.
    """
    try:
        import questionary
    except ImportError:
        print("questionary is required for TUI. Install with: pip install questionary")
        return False

    config = ScoutConfig()
    raw = config._raw
    triggers = raw.get("triggers", {}) or {}
    limits = raw.get("limits", {}) or {}
    patterns = list(triggers.get("patterns") or [])

    TRIGGER_CHOICES = ["manual", "on-save", "on-commit", "on-push", "disabled"]
    COST_CHOICES = ["0.01", "0.02", "0.05", "0.10", "0.25", "0.50", "1.00"]

    def _format_pattern(i: int, p: dict) -> str:
        pat = p.get("pattern", "")
        trig = p.get("trigger", "on-commit")
        mc = p.get("max_cost")
        cost_str = f" ${mc}" if mc is not None else ""
        return f"{i+1}. {pat}  [{trig}]{cost_str}"

    while True:
        default_trigger = str(triggers.get("default") or "on-commit")
        max_per = str(limits.get("max_cost_per_event") or 0.05)
        hourly = str(limits.get("hourly_budget") or 1.0)

        action = questionary.select(
            "Configuration",
            choices=[
                questionary.Choice("1. Edit default trigger", value="default"),
                questionary.Choice("2. Edit patterns", value="patterns"),
                questionary.Choice("3. Edit limits", value="limits"),
                questionary.Separator(),
                questionary.Choice("Save", value="save"),
                questionary.Choice("Cancel", value="cancel"),
                questionary.Choice("Reset to defaults", value="reset"),
            ],
        ).ask()

        if action is None:
            return False
        if action == "cancel":
            return False
        if action == "save":
            config._raw = raw
            path = config.get_project_config_path()
            if not path.parent.exists():
                path = config.get_user_config_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                import yaml

                with open(path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(raw, f, default_flow_style=False, sort_keys=False)
                print(f"Saved to {path}")
            except Exception as e:
                print(f"Failed to save: {e}")
            return True
        if action == "reset":
            raw["triggers"] = dict(DEFAULT_CONFIG["triggers"])
            raw["limits"] = dict(DEFAULT_CONFIG["limits"])
            triggers = raw["triggers"]
            limits = raw["limits"]
            patterns = list(triggers.get("patterns") or [])
            print("Reset to defaults.")
            continue

        if action == "default":
            new_default = questionary.select(
                "Default trigger",
                choices=TRIGGER_CHOICES,
                default=default_trigger,
            ).ask()
            if new_default:
                triggers["default"] = new_default
            continue

        if action == "limits":
            new_max = questionary.select(
                "Max cost per event ($)",
                choices=COST_CHOICES,
                default=max_per,
            ).ask()
            if new_max:
                limits["max_cost_per_event"] = float(new_max)
            new_hourly = questionary.select(
                "Hourly budget ($)",
                choices=["0.50", "1.00", "2.00", "5.00", "10.00"],
                default=hourly,
            ).ask()
            if new_hourly:
                limits["hourly_budget"] = min(
                    float(new_hourly), HARD_MAX_HOURLY_BUDGET
                )
            continue

        if action == "patterns":
            while True:
                choices = [
                    questionary.Choice(_format_pattern(i, p), value=i)
                    for i, p in enumerate(patterns)
                ]
                choices.extend([
                    questionary.Separator(),
                    questionary.Choice("Add pattern", value="add"),
                    questionary.Choice("Back", value="back"),
                ])
                sel = questionary.select("Patterns", choices=choices).ask()
                if sel is None or sel == "back":
                    break
                if sel == "add":
                    pat = questionary.text("Pattern (glob, e.g. vivarium/**/*.py):").ask()
                    if not pat:
                        continue
                    trig = questionary.select(
                        "Trigger",
                        choices=TRIGGER_CHOICES,
                        default="on-commit",
                    ).ask()
                    if not trig:
                        continue
                    mc = questionary.select(
                        "Max cost (optional)",
                        choices=["None"] + COST_CHOICES,
                        default="None",
                    ).ask()
                    entry = {"pattern": pat.strip(), "trigger": trig}
                    if mc and mc != "None":
                        entry["max_cost"] = float(mc)
                    patterns.append(entry)
                    triggers["patterns"] = patterns
                    continue
                for i, p in enumerate(patterns):
                    if i == sel:
                        edit = questionary.select(
                            f"Edit {_format_pattern(i, p)}",
                            choices=["Remove", "Edit trigger", "Edit max cost", "Back"],
                        ).ask()
                        if edit == "Remove":
                            patterns.pop(i)
                            triggers["patterns"] = patterns
                        elif edit == "Edit trigger":
                            new_trig = questionary.select(
                                "Trigger",
                                choices=TRIGGER_CHOICES,
                                default=p.get("trigger", "on-commit"),
                            ).ask()
                            if new_trig:
                                p["trigger"] = new_trig
                        elif edit == "Edit max cost":
                            new_mc = questionary.select(
                                "Max cost",
                                choices=["None"] + COST_CHOICES,
                                default=str(p.get("max_cost", "None")),
                            ).ask()
                            if new_mc == "None":
                                p.pop("max_cost", None)
                            elif new_mc:
                                p["max_cost"] = float(new_mc)
                        break
            continue

    return False
