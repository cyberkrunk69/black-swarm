"""
Shared LLM cost estimation with official Groq pricing.

Source: https://console.groq.com/docs/models
"""

import logging

logger = logging.getLogger(__name__)

# Official Groq production pricing (per 1M tokens) as of 2026-02-13
# Source: https://console.groq.com/docs/models
GROQ_MODELS = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "openai/gpt-oss-120b": {"input": 0.15, "output": 0.60},  # CORRECTED
    "openai/gpt-oss-20b": {"input": 0.075, "output": 0.30},  # NEW
    # Preview models (add if used in codebase):
    # "meta-llama/llama-4-scout-17b-16e-instruct": {"input": 0.11, "output": 0.34},
    # "qwen/qwen3-32b": {"input": 0.29, "output": 0.59},
}

# Compound systems require special handling – no fixed per-token pricing
COMPOUND_MODELS = {"groq/compound", "groq/compound-mini"}


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """
    Returns cost in USD. For compound models, uses conservative fallback with warning.
    """
    if model_id in COMPOUND_MODELS:
        # Compound pricing is dynamic (tools + models). Use conservative fallback + log warning.
        logger.warning(
            "Compound model '%s' has dynamic pricing. Using conservative $1.00/1M token fallback. "
            "Actual cost may vary based on tool usage.",
            model_id,
        )
        return (input_tokens + output_tokens) * 1.0 / 1_000_000

    pricing = GROQ_MODELS.get(model_id)
    if not pricing:
        logger.warning(
            "Unknown model '%s'. Using conservative $1.00/1M token fallback. "
            "Update GROQ_MODELS in llm_cost.py with official pricing.",
            model_id,
        )
        return (input_tokens + output_tokens) * 1.0 / 1_000_000

    return (
        input_tokens * pricing["input"] + output_tokens * pricing["output"]
    ) / 1_000_000


def rough_token_count(text: str) -> int:
    """
    Fast approximation: word count × 1.3 (accounts for punctuation/symbols in logs/code).
    Calibrated for CI logs and English text. Not suitable for CJK/minified JSON.
    """
    if not text:
        return 0
    return max(1, int(len(text.split()) * 1.3))
