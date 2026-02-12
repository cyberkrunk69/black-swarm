"""
Scout LLM client — Groq API for navigation.

Pluggable for testing; uses GROQ_API_KEY from env or runtime config.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

# Groq pricing (per 1M tokens)
COST_8B_INPUT = 0.05
COST_8B_OUTPUT = 0.08
COST_70B_INPUT = 0.59
COST_70B_OUTPUT = 0.79


@dataclass
class NavResponse:
    """Raw LLM response for navigation."""

    content: str
    cost_usd: float
    model: str
    input_tokens: int
    output_tokens: int


def _get_groq_api_key() -> Optional[str]:
    """Get Groq API key from env or runtime config."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        from vivarium.runtime import config as runtime_config

        return runtime_config.get_groq_api_key()
    except ImportError:
        return None


async def call_groq_async(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    system: Optional[str] = None,
    llm_client: Optional[Callable] = None,
) -> NavResponse:
    """
    Call Groq API for navigation. Uses llm_client if provided (for testing).
    """
    if llm_client:
        return await llm_client(prompt, model=model, system=system)

    api_key = _get_groq_api_key()
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Set it in environment or configure via runtime."
        )

    try:
        import httpx
    except ImportError:
        raise RuntimeError("httpx required for scout-nav. Install with: pip install httpx")

    url = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    resp.raise_for_status()
    data = resp.json()

    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = msg.get("content", "").strip()

    usage = data.get("usage", {})
    input_t = int(usage.get("input_tokens", 0))
    output_t = int(usage.get("output_tokens", 0))

    if model == "llama-3.1-8b-instant":
        cost = input_t / 1_000_000 * COST_8B_INPUT + output_t / 1_000_000 * COST_8B_OUTPUT
    else:
        cost = input_t / 1_000_000 * COST_70B_INPUT + output_t / 1_000_000 * COST_70B_OUTPUT

    return NavResponse(
        content=content,
        cost_usd=cost,
        model=model,
        input_tokens=input_t,
        output_tokens=output_t,
    )
