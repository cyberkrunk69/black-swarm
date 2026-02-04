# tools/git/__init__.py
"""
Git tool metadata.
Wraps common git commands such as clone, commit, push, and status.
"""

metadata = {
    "name": "git",
    "description": "Perform basic Git operations: clone repositories, commit changes, push to remotes, and query status.",
    "input_schema": {
        "command": {"type": "string", "enum": ["clone", "commit", "push", "status"]},
        "repository_url": {"type": "string"},
        "branch": {"type": "string"},
        "message": {"type": "string"}  # required for commit
    },
    "output_schema": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "details": {"type": "string"}
    },
    "usage_count": 0,
    "success_rate": 1.0
}