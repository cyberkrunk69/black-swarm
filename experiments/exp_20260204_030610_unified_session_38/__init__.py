"""
Experiment package for unified session 38.
Registers admin API blueprint.
"""

from .api.admin_commands import admin_bp

def register_blueprints(app):
    """
    Call this from the main application to add the admin command routes.
    """
    app.register_blueprint(admin_bp)