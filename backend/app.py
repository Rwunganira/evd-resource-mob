import os
from flask import Flask, jsonify, redirect, url_for, render_template
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from routes.partners import partners_bp
from routes.resources import resources_bp
from routes.activities import activities_bp
from routes.reports import reports_bp
from routes.funding_gap import funding_gap_bp
from routes.partner_reports import partner_reports_bp
from routes.imports import imports_bp
from views.partners import partners_view_bp
from views.resources import resources_view_bp
from views.activities import activities_view_bp
from views.sitreps import sitreps_view_bp
from views.auth import auth_bp
from views.users import users_view_bp

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "evd-response-secret-key")
    db_url = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(os.path.dirname(__file__), 'evd_response.db')}")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
    )

    init_db(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        return {"streamlit_url": os.getenv("STREAMLIT_URL", "http://localhost:8501")}

    # JSON API blueprints (consumed by Streamlit)
    app.register_blueprint(partners_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(funding_gap_bp)
    app.register_blueprint(partner_reports_bp)
    app.register_blueprint(imports_bp)

    # HTML view blueprints (data management UI)
    app.register_blueprint(auth_bp)
    app.register_blueprint(partners_view_bp)
    app.register_blueprint(resources_view_bp)
    app.register_blueprint(activities_view_bp)
    app.register_blueprint(sitreps_view_bp)
    app.register_blueprint(users_view_bp)

    @app.route("/")
    def index():
        return redirect(url_for("partners_view.list_partners"))

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "data": None, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"status": "error", "data": None, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"status": "error", "data": None, "message": "Internal server error"}), 500

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "success",
            "data": {"healthy": True},
            "message": "EVD Mobilization API running",
        })

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"Starting EVD Mobilization API on port {port}...")
    app.run(debug=debug, host="0.0.0.0", port=port)
