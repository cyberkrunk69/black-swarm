"""
model_policy.py
---------------
Model tier selection + internal cost weighting.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple


MODEL_TIER_MAP: Dict[str, str] = {
    "low": "llama-3.1-8b-instant",
    "medium": "llama-3.3-70b-versatile",
    "high": "openai/gpt-oss-20b",
    "max": "openai/gpt-oss-120b",
}

MODEL_TIER_MULTIPLIERS: Dict[str, float] = {
    "low": 0.7,
    "medium": 1.0,
    "high": 1.4,
    "max": 1.8,
}

MODEL_ALIAS_TO_TIER = {
    "tiny": "low",
    "small": "low",
    "compact": "low",
    "eco": "low",
    "efficient": "low",
    "standard": "medium",
    "default": "medium",
    "large": "high",
    "xl": "high",
    "ultra": "max",
    "iqmax": "max",
    "iq_max": "max",
    "max": "max",
}

MODEL_ID_TO_TIER = {
    "llama-3.1-8b-instant": "low",
    "llama-3.3-70b-versatile": "medium",
    "openai/gpt-oss-20b": "high",
    "openai/gpt-oss-120b": "max",
}


def normalize_tier(tier: Optional[str]) -> Optional[str]:
    if not tier:
        return None
    cleaned = tier.strip().lower().replace("-", "_").replace(" ", "_")
    return MODEL_ALIAS_TO_TIER.get(cleaned, cleaned)


def infer_tier_from_model(model_id: Optional[str]) -> str:
    if not model_id:
        return "medium"
    return MODEL_ID_TO_TIER.get(model_id, "medium")


def get_tier_multiplier(tier: Optional[str]) -> float:
    tier = normalize_tier(tier)
    if not tier:
        return MODEL_TIER_MULTIPLIERS["medium"]
    return MODEL_TIER_MULTIPLIERS.get(tier, MODEL_TIER_MULTIPLIERS["medium"])


def resolve_model_choice(
    *,
    model: Optional[str],
    model_tier: Optional[str],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve model + tier into a concrete model id + normalized tier.
    """
    tier = normalize_tier(model_tier)
    if model:
        return model, infer_tier_from_model(model)
    if tier and tier in MODEL_TIER_MAP:
        return MODEL_TIER_MAP[tier], tier
    return None, ""


__all__ = [
    "MODEL_TIER_MAP",
    "MODEL_TIER_MULTIPLIERS",
    "normalize_tier",
    "infer_tier_from_model",
    "get_tier_multiplier",
    "resolve_model_choice",
]
