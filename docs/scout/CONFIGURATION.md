# Scout Configuration

Scout uses layered YAML configuration with **hard safety caps** — users control their destiny but not their budget ceiling.

## File Locations (precedence order)

1. **`~/.scout/config.yaml`** — User global (applies to all projects)
2. **`.scout/config.yaml`** — Project local (gitignored, overrides user)
3. **Environment variables** — Override YAML (e.g. `SCOUT_MAX_COST_PER_EVENT=0.05`)
4. **Hardcoded safety caps** — Non-negotiable ceiling (never overridden)

## YAML Schema

```yaml
triggers:
  default: "on-commit"  # manual | on-save | on-commit | on-push | disabled

  patterns:
    - pattern: "vivarium/runtime/*.py"
      trigger: "on-save"
      max_cost: 0.02

    - pattern: "tests/*"
      trigger: "manual"

    - pattern: "docs/*.md"
      trigger: "disabled"

limits:
  max_cost_per_event: 0.05      # User setting ($ per trigger)
  hourly_budget: 1.00           # User setting
  hard_safety_cap: 10.00        # NON-OVERRIDABLE ceiling

models:
  scout_nav: "llama-3.1-8b"
  max_for_auto: "llama-3.1-8b"  # Never auto-escalate

notifications:
  on_validation_failure: "alert"  # alert | escalate | skip
```

## Trigger Resolution

1. **Patterns** — First match wins (glob patterns: `*` = any chars except `/`, `**` = any path segments)
2. **Default** — Fall back to `triggers.default` if no pattern matches

## Environment Variables

| Variable | Maps to | Example |
|----------|---------|---------|
| `SCOUT_MAX_COST_PER_EVENT` | `limits.max_cost_per_event` | `0.05` |
| `SCOUT_HOURLY_BUDGET` | `limits.hourly_budget` | `1.00` |
| `SCOUT_DEFAULT_TRIGGER` | `triggers.default` | `on-commit` |
| `SCOUT_ON_VALIDATION_FAILURE` | `notifications.on_validation_failure` | `alert` |

## Hard Safety Caps (non-negotiable)

| Constant | Value | Description |
|----------|-------|-------------|
| `HARD_MAX_COST_PER_EVENT` | $1.00 | Never allow >$1 per trigger |
| `HARD_MAX_HOURLY_BUDGET` | $10.00 | Emergency brake |
| `HARD_MAX_AUTO_ESCALATIONS` | 3 | Prevent retry loops |

User config **cannot** override these.

## CLI

```bash
# Open config in $EDITOR
python -m vivarium.scout config

# Print value
python -m vivarium.scout config --get triggers.default

# Set value
python -m vivarium.scout config --set limits.hourly_budget 2.00

# Interactive TUI (requires questionary)
python -m vivarium.scout config --tui

# Validate YAML syntax
python -m vivarium.scout config --validate

# Show merged effective config
python -m vivarium.scout config --effective
```

## Python API

```python
from vivarium.scout.config import ScoutConfig, TriggerConfig

config = ScoutConfig()

# Resolve trigger for a file
tc = config.resolve_trigger(Path("vivarium/runtime/foo.py"))
# tc.type == "on-save", tc.max_cost == 0.02

# Check if we should process (estimated cost, hourly spend)
if config.should_process(0.03, file_path=Path("foo.py"), hourly_spend=0.5):
    # proceed with LLM call
    pass

# Current effective config (for audit logging)
audit_config = config.to_dict()
```

## TUI (Terminal UI)

Install `questionary` for the interactive config editor:

```bash
pip install questionary
python -m vivarium.scout config --tui
```

The TUI lets you edit triggers, patterns, and limits without touching YAML.
