import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Configuration constants
MAX_CONTENT_LENGTH_BYTES = 16 * 1024 * 1024  # 16MB

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = "False"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SQLALCHEMY_SESSION_OPTIONS"] = {"autoflush": False}
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_BYTES

    db.init_app(app)
    migrate.init_app(app, db)
    
    # Force disable autoflush directly on the session
    with app.app_context():
        db.session.autoflush = False
        print(f"SQLAlchemy session autoflush after manual set: {db.session.autoflush}")
        print(f"App config SQLALCHEMY_SESSION_OPTIONS: {app.config.get('SQLALCHEMY_SESSION_OPTIONS')}")

    from backend.api import register_blueprints
    register_blueprints(app)
    
    # Register CLI commands
    from backend.cli import register_commands
    register_commands(app)

    return app
