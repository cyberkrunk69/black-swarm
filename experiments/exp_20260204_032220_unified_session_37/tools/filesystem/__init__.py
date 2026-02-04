# tools/filesystem/__init__.py
"""
Filesystem tool metadata.
Provides basic file‑system operations (e.g., read, write, list).
"""

metadata = {
    "name": "filesystem",
    "description": "Interact with the local file system: read, write, delete, and list files and directories.",
    "input_schema": {
        "operation": {"type": "string", "enum": ["read", "write", "delete", "list"]},
        "path": {"type": "string"},
        "content": {"type": "string"}  # required for write operation
    },
    "output_schema": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {"type": "string"}  # file content for read or directory listing for list
    },
    "usage_count": 0,
    "success_rate": 1.0
}