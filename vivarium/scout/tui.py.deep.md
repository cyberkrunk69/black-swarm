# tui.py

## Function: `_render_header`

Detailed documentation (deep stub).

```python
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
     
```

## Function: `run_config_tui`

Detailed documentation (deep stub).

```python
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

    TRIGGER_CHOICES = ["manual
```

## Function: `_format_pattern`

Detailed documentation (deep stub).

```python
    def _format_pattern(i: int, p: dict) -> str:
        pat = p.get("pattern", "")
        trig = p.get("trigger", "on-commit")
        mc = p.get("max_cost")
        cost_str = f" ${mc}" if mc is not None else ""
        return f"{i+1}. {pat}  [{trig}]{cost_str}"
```
