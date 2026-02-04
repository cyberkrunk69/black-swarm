# tools/filesystem/file_ops.py
"""
Simple filesystem utility tool.
"""

TOOL_INFO = {
    "name": "FileOperations",
    "description": "Provides basic file system operations such as read, write, and list directory contents.",
    "input_schema": {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "list"]},
            "path": {"type": "string"},
            "content": {"type": "string"}  # required only for write
        },
        "required": ["operation", "path"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "data": {"type": "string"}
        },
        "required": ["status"]
    },
    "usage_count": 0,
    "success_rate": 0.0
}