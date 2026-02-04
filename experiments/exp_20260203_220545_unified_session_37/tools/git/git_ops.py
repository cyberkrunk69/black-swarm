# tools/git/git_ops.py
"""
Utility for basic git interactions.
"""

TOOL_INFO = {
    "name": "GitOperations",
    "description": "Executes simple git commands such as clone, status, and pull.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "enum": ["clone", "status", "pull"]},
            "repository": {"type": "string"},
            "target_dir": {"type": "string"}
        },
        "required": ["command"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "returncode": {"type": "integer"}
        },
        "required": ["stdout", "stderr", "returncode"]
    },
    "usage_count": 0,
    "success_rate": 0.0
}