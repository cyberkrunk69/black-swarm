"""
Filesystem tool metadata.
"""

TOOL_INFO = {
    "description": "Provides basic file system operations such as read, write, delete, and list files.",
    "schema": {
        "input": {
            "operation": "str",  # e.g., 'read', 'write', 'delete', 'list'
            "path": "str",
            "content": "str (optional, for write)"
        },
        "output": {
            "status": "str",  # e.g., 'success' or error message
            "data": "str (optional, for read/list)"
        }
    },
    "usage_count": 0,
    "success_rate": 0.0,
}