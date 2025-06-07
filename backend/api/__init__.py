from flask import Blueprint
from backend.api.users import users_bp
from backend.api.sessions import sessions_bp
from backend.api.surveys import surveys_bp
from backend.api.searches import searches_bp
from backend.api.search_results import search_results_bp
from backend.api.search_data import search_data_bp

def register_blueprints(app):
    """Register all API blueprints with the Flask app"""
    app.register_blueprint(users_bp, url_prefix='/api')
    app.register_blueprint(sessions_bp, url_prefix='/api')
    app.register_blueprint(surveys_bp, url_prefix='/api')
    app.register_blueprint(searches_bp, url_prefix='/api')
    app.register_blueprint(search_results_bp, url_prefix='/api')
    app.register_blueprint(search_data_bp, url_prefix='/api')
