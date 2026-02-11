"""Registry of Flask blueprints for the control panel. Each (bp, url_prefix) is registered on the app."""
from __future__ import annotations

# [BLUEPRINTS_START]
from vivarium.runtime.control_panel.blueprints.groq_key import groq_key_bp
from vivarium.runtime.control_panel.blueprints.identities import identities_bp
from vivarium.runtime.control_panel.blueprints.logs import logs_bp
from vivarium.runtime.control_panel.blueprints.messages import messages_bp
from vivarium.runtime.control_panel.blueprints.spawner import spawner_bp
from vivarium.runtime.control_panel.blueprints.stop_toggle import stop_toggle_bp

BLUEPRINT_SPECS: list[tuple] = [
    (groq_key_bp, ""),
    (stop_toggle_bp, ""),
    (identities_bp, ""),
    (messages_bp, ""),
    (logs_bp, ""),
    (spawner_bp, ""),
]


def register_blueprints(app):
    """Register all control panel blueprints on the Flask app."""
    for bp, url_prefix in BLUEPRINT_SPECS:
        kwargs = {"url_prefix": url_prefix} if url_prefix else {}
        app.register_blueprint(bp, **kwargs)
