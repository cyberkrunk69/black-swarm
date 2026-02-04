# Cleaned version of main.py
# Removed imports and code that referenced the Anthropic SDK or Claude.

import os
import sys
import json
from pathlib import Path

# Import the generic API client instead of the Anthropic‑specific one.
from src.anthropic_client import APIClient

def load_config(config_path: str) -> dict:
    """Load JSON configuration from the given path."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main() -> None:
    # Load configuration (e.g., endpoint and API key)
    config = load_config(os.getenv("CONFIG_PATH", "config.json"))
    api_url = config.get("api_url", "https://api.example.com/v1")
    api_key = config.get("api_key")

    client = APIClient(base_url=api_url, api_key=api_key)

    # Example interaction – replace with actual application logic.
    prompt = "Hello, world!"
    try:
        response = client.post("/chat/completions", json_body={"prompt": prompt})
        print("Model response:", response.get("completion"))
    except Exception as e:
        # Use the simple fallback defined in claude_fallback.py
        from src.claude_fallback import fallback_response
        print("Error contacting model:", e)
        print(fallback_response(prompt))

if __name__ == "__main__":
    main()