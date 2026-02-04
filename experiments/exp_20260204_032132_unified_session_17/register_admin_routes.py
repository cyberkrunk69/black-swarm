"""
Utility to register the admin command routes with the main Flask app.
Import and call `register_admin_routes(app)` from your application entry point.
"""

def register_admin_routes(app):
    from .admin_commands import admin_bp
    app.register_blueprint(admin_bp)