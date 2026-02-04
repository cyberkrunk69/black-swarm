"""
Git tool metadata.
"""

TOOL_INFO = {
    "description": "Wraps common Git commands like clone, commit, push, pull, and status.",
    "schema": {
        "input": {
            "command": "str",  # e.g., 'clone', 'commit', 'push', 'pull', 'status'
            "repository": "str (optional, for clone)",
            "message": "str (optional, for commit)",
            "branch": "str (optional)",
            "options": "list[str] (optional)"
        },
        "output": {
            "status": "str",  # 'success' or error description
            "details": "str (optional)"
        }
    },
    "usage_count": 0,
    "success_rate": 0.0,
}