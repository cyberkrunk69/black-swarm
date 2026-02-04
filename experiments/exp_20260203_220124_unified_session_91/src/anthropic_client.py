# Cleaned version of anthropic_client.py
# This module provides a generic HTTP client for interacting with language model APIs.
# All references to the Anthropic SDK and Claude have been removed.

import json
import os
import requests
from typing import Any, Dict, Optional

class APIClient:
    """
    Simple wrapper around the requests library to interact with a generic LLM endpoint.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("API_KEY")
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(
            method=method,
            url=url,
            json=json_body,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, *, json_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("POST", endpoint, json_body=json_body)

    def get(self, endpoint: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("GET", endpoint, params=params)

# Example usage (to be removed or adapted by the consuming application):
# client = APIClient(base_url="https://api.example.com/v1")
# response = client.post("/chat/completions", json_body={"prompt": "Hello"})
# print(response)