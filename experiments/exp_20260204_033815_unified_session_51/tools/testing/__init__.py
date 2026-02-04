"""
Testing tool metadata.
"""

TOOL_INFO = {
    "description": "Runs automated tests, collects results, and reports pass/fail statistics.",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_suite": {"type": "string"},
            "timeout_seconds": {"type": "integer", "minimum": 1}
        },
        "required": ["test_suite"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "passed": {"type": "integer"},
            "failed": {"type": "integer"},
            "report": {"type": "string"}
        },
        "required": ["success", "passed", "failed"]
    },
    "usage_count": 0,
    "success_rate": 1.0
}