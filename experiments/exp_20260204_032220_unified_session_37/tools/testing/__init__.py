# tools/testing/__init__.py
"""
Testing tool metadata.
Facilitates execution of unit or integration test suites and reports results.
"""

metadata = {
    "name": "testing",
    "description": "Run automated test suites (e.g., pytest) and return a summary of passed/failed tests.",
    "input_schema": {
        "test_command": {"type": "string"},
        "test_path": {"type": "string"}
    },
    "output_schema": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "summary": {"type": "string"}
    },
    "usage_count": 0,
    "success_rate": 1.0
}