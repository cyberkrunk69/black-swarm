"""
Testing tool – utilities for running unit/integration tests.
"""

metadata = {
    "name": "TestingTool",
    "description": "Runs specified test suites and returns aggregated results.",
    "input_schema": {
        "suite_path": {"type": "string"},
        "verbose": {"type": "boolean", "optional": True}
    },
    "output_schema": {
        "passed": {"type": "integer"},
        "failed": {"type": "integer"},
        "details": {"type": "string", "optional": True}
    },
    "usage_count": 0,
    "success_rate": 0.0
}