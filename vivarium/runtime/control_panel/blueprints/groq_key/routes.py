"""Groq API key blueprint: read and configure key via runtime config (no filesystem)."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from vivarium.runtime import config as runtime_config

bp = Blueprint('groq_key', __name__, url_prefix='/api')


def _mask_secret(secret: str) -> str:
    value = (secret or "").strip()
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}...{value[-4:]}"


def _reload_groq_runtime_clients() -> None:
    """Reset Groq client singleton so new key is used immediately."""
    try:
        from vivarium.runtime import groq_client
        groq_client._groq_engine = None
    except Exception:
        pass


def _ensure_groq_key_loaded() -> dict:
    """Get key status from runtime config. Keys forage at runtime via get_secret."""
    live_key = (runtime_config.get_secret("GROQ_API_KEY") or "").strip()
    if live_key:
        return {"configured": True, "key": live_key, "source": "env"}
    return {"configured": False, "key": "", "source": None}


@bp.route('/groq_key', methods=['GET'])
def get_groq_key():
    """GET /api/groq_key - Return masked key status."""
    state = _ensure_groq_key_loaded()
    return jsonify(
        {
            "success": True,
            "configured": state["configured"],
            "source": state["source"],
            "masked_key": _mask_secret(state["key"]) if state["configured"] else None,
        }
    )


@bp.route('/groq_key', methods=['POST'])
def set_groq_key():
    """POST /api/groq_key - Configure key for current runtime (env or this session)."""
    data = request.json or {}
    api_key = str(data.get("api_key", "")).strip()
    if not api_key:
        return jsonify({"success": False, "error": "api_key is required"}), 400
    if len(api_key) < 16:
        return jsonify({"success": False, "error": "api_key is too short"}), 400
    if len(api_key) > 256:
        return jsonify({"success": False, "error": "api_key is too long"}), 400

    runtime_config.set_groq_api_key(api_key)
    _reload_groq_runtime_clients()
    return jsonify(
        {
            "success": True,
            "configured": True,
            "masked_key": _mask_secret(api_key),
            "source": "env",
        }
    )


@bp.route('/groq_key', methods=['DELETE'])
def delete_groq_key():
    """DELETE /api/groq_key - Clear key from current runtime."""
    runtime_config.set_groq_api_key(None)
    _reload_groq_runtime_clients()
    return jsonify({"success": True, "configured": False})
