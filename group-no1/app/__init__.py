import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from config import config_by_name, Config
from app.extensions import db, login_manager, csrf, limiter


def create_app(config_name: str = "default") -> Flask:
    """Application factory for Group No1 Global Lost & Found Management System."""
    app = Flask(__name__)
    
    # Load configuration
    cfg = config_by_name.get(config_name, Config)
    app.config.from_object(cfg)

    # Ensure required runtime directories exist
    upload_path = Path(app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register Blueprints
    from app.main import main_bp
    from app.auth import auth_bp
    from app.items import items_bp
    from app.claims import claims_bp
    from app.dashboard import dashboard_bp
    from app.notifications import notifications_bp
    from app.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(claims_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(api_bp)

    # Context processor to inject global template helpers
    @app.context_processor
    def inject_globals():
        return {
            "app_name": app.config.get("APP_NAME", "Group No1"),
            "app_type": app.config.get("APP_TYPE", "Global Lost & Found Management System"),
            "app_tagline": app.config.get("APP_TAGLINE", "Lost Something? Found Something? Let's Bring It Back."),
            "app_page_title": app.config.get("APP_PAGE_TITLE", "Group No1 — Global Lost & Found"),
            "app_footer": app.config.get("APP_FOOTER", "© Group No1 | Global Lost & Found Management System"),
            "current_year": datetime.now().year,
        }

    # Custom Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Bad Request", "message": str(error)}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden", "message": "You do not have permission to access this resource."}), 403
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def page_not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not Found", "message": "Resource was not found."}), 404
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal Server Error", "message": "A server error occurred."}), 500
        return render_template("errors/500.html", error=error), 500

    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Item, ItemImage, Claim, Notification, Message
        return {
            "db": db,
            "User": User,
            "Item": Item,
            "ItemImage": ItemImage,
            "Claim": Claim,
            "Notification": Notification,
            "Message": Message,
        }

    return app
