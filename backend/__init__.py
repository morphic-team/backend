import os
import sentry_sdk
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

sentry_sdk.init(
    dsn="https://9eeb4684dc1ab49e736b24f3bbc8c789@sentry.morphs.io/2",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


def create_app(environment="dev"):
    app = Flask(__name__)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = "False"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    db.init_app(app)

    from backend.api import api

    app.register_blueprint(api, url_prefix="/api")

    return app
