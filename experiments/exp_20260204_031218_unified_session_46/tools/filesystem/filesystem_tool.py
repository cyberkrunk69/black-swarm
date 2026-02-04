"""
Filesystem tool – basic file operations abstraction.
"""

metadata = {
    "name": "FilesystemTool",
    "description": "Provides high‑level operations for reading, writing and listing files on the local filesystem.",
    "input_schema": {
        "operation": {"type": "string", "enum": ["read", "write", "list"]},
        "path": {"type": "string"},
        "content": {"type": "string", "optional": True}
    },
    "output_schema": {
        "status": {"type": "string"},
        "data": {"type": "any", "optional": True}
    },
    "usage_count": 0,
    "success_rate": 0.0
}