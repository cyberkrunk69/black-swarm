# tools/user_contributed/custom_tool.py
"""
Example of a user‑contributed tool.
"""

TOOL_INFO = {
    "name": "CustomUserTool",
    "description": "A placeholder for a user‑provided utility; demonstrates extensibility.",
    "input_schema": {
        "type": "object",
        "properties": {
            "payload": {"type": "string"}
        },
        "required": ["payload"]
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        },
        "required": ["result"]
    },
    "usage_count": 0,
    "success_rate": 0.0
}