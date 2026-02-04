"""
Git tool metadata.
"""

TOOL_INFO = {
    "description": "Encapsulates common Git operations: clone, commit, push, pull, and status.",
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["clone", "commit", "push", "pull", "status"]},
            "repo_url": {"type": "string"},
            "branch": {"type": "string"},
            "message": {"type": "string"}  # required for commit
        },
        "required": ["operation"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "details": {"type": "string"}
        },
        "required": ["success"]
    },
    "usage_count": 0,
    "success_rate": 1.0
}