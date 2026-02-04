"""
Filesystem tool metadata.
"""

TOOL_INFO = {
    "description": "Provides basic file system operations such as read, write, list, and delete files.",
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "list", "delete"]},
            "path": {"type": "string"},
            "content": {"type": "string"}  # required for write
        },
        "required": ["operation", "path"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "string"}  # file content for read or listing result
        },
        "required": ["success"]
    },
    "usage_count": 0,
    "success_rate": 1.0
}