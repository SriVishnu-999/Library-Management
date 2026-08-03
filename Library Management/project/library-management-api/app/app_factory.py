"""Application factory and Flask app initialization."""

from flask import Flask, jsonify
from config import get_config
from app.database import init_pool, close_pool, close_db
from app.controllers.book_controller import books_bp
from app.controllers.member_controller import members_bp
from app.controllers.issue_controller import issue_bp


def create_app(config_class=None):
    """
    Application factory pattern.
    Creates and configures the Flask app, registers blueprints,
    and sets up error handlers and teardown hooks.
    """
    app = Flask(__name__)

    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    _register_blueprints(app)
    _register_error_handlers(app)
    _register_teardown(app)

    with app.app_context():
        init_pool()

    return app


def _register_blueprints(app):
    """Register all controller blueprints."""
    app.register_blueprint(books_bp)
    app.register_blueprint(members_bp)
    app.register_blueprint(issue_bp)


def _register_error_handlers(app):
    """Register global error handlers for consistent API responses."""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Resource not found",
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "message": "Method not allowed for this endpoint",
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "message": "Bad request",
        }), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "message": "Internal server error",
        }), 500


def _register_teardown(app):
    """Register teardown hooks for connection cleanup."""

    @app.teardown_request
    def teardown_db(exception):
        close_db(exception)

    @app.teardown_appcontext
    def teardown_pool(exception):
        if exception is not None:
            close_pool()
