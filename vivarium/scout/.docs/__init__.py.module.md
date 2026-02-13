## Purpose
The vivarium.scout package is a tool for auditing and logging system events, with features for rotating logs, calculating hourly spend, and tracking accuracy metrics.

## Components
### Ingress
- **audit.py**: Handles auditing and logging system events, including generating unique session IDs, rotating logs, and calculating hourly spend.
- **git_analyzer.py**: Analyzes Git repository data, including getting changed files, Git version, and commit hashes.

### Processing
- **config.py**: Manages configuration settings, including project and user configuration paths, and validating YAML configuration files.
- **router.py**: Routes system events to appropriate handlers, including Git commits and on-commit actions.

### Egress
- **tui.py**: Handles user interaction through a Text User Interface (TUI), including running configuration TUIs.
- **validator.py**: Validates system data, including location validation and accuracy metrics calculation.

## Key Invariants
- **Plain-text Git workflow**: The system relies on plain-text Git workflow, as evident from the use of `git_analyzer.py` and `router.py`.
- **No external dependencies**: The system does not have any external dependencies, as evident from the lack of external library imports in the traced roles.