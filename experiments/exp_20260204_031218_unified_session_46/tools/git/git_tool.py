"""
Git tool – simple wrapper around common git commands.
"""

metadata = {
    "name": "GitTool",
    "description": "Executes basic git operations such as clone, commit, and push in a sandboxed environment.",
    "input_schema": {
        "command": {"type": "string", "enum": ["clone", "commit", "push", "status"]},
        "repo_url": {"type": "string", "optional": True},
        "message": {"type": "string", "optional": True}
    },
    "output_schema": {
        "result": {"type": "string"},
        "error": {"type": "string", "optional": True}
    },
    "usage_count": 0,
    "success_rate": 0.0
}