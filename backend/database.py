import os
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    db_path = os.path.join(os.path.dirname(__file__), "evd_response.db")
    default_uri = f"sqlite:///{db_path}"
    uri = os.getenv("DATABASE_URL", default_uri)
    # Heroku PostgreSQL provides postgres:// — SQLAlchemy requires postgresql://
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", uri)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
