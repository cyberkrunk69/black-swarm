"""
Testing tool metadata.
"""

TOOL_INFO = {
    "description": "Executes unit/integration tests and reports results.",
    "schema": {
        "input": {
            "test_suite": "str",  # path or identifier of the test suite
            "verbosity": "int (optional)",
            "timeout": "int (optional, seconds)"
        },
        "output": {
            "passed": "int",
            "failed": "int",
            "errors": "list[str]",
            "duration_seconds": "float"
        }
    },
    "usage_count": 0,
    "success_rate": 0.0,
}