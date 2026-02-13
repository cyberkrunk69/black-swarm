## Purpose
The vivarium.scout.cli package is a command-line interface (CLI) for the Vivarium Scout system, providing tools for auditing, validation, and navigation within the system.

## Components
### Ingress
- `brief.py`: Handles command-line arguments and parses them using `argparse`.
- `nav.py`: Parses command-line arguments and provides navigation functionality.

### Processing
- `brief.py`: Generates a brief report or document based on gathered information from Git context, dependencies, and complexity calculations.
- `ci_guard.py`: Runs a CI guard to ensure the system is in a valid state.
- `doc_sync.py`: Synchronizes documentation files.
- `index.py`: Builds and updates the index of files in the system.
- `main.py`: Configures and validates the system.
- `roast.py`: Generates a report based on audit logs.
- `status.py`: Runs a status check on the system.

### Egress
- `brief.py`: Writes the generated brief report to a file.
- `index.py`: Outputs the updated index to a file.
- `roast.py`: Outputs the generated report to the console.
- `status.py`: Outputs the status check result to the console.

## Key Invariants
- The system uses a plain-text Git workflow.
- The system does not have any external dependencies.
- The system relies on the `vivarium` and `scout` modules for configuration, validation, and routing.