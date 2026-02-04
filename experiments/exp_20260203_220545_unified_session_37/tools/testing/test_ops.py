# tools/testing/test_ops.py
"""
Simple testing utility.
"""

TOOL_INFO = {
    "name": "TestRunner",
    "description": "Runs unit tests and returns pass/fail statistics.",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_path": {"type": "string"},
            "verbosity": {"type": "integer", "minimum": 0, "maximum": 2}
        },
        "required": ["test_path"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "total": {"type": "integer"},
            "passed": {"type": "integer"},
            "failed": {"type": "integer"},
            "details": {"type": "string"}
        },
        "required": ["total", "passed", "failed"]
    },
    "usage_count": 0,
    "success_rate": 0.0
}