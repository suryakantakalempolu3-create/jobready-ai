import secrets
from flask import Flask, jsonify, request, session, render_template
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from config import Config
from .models import db


def create_app(config=None, seed=True):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    # ---- MySQL (Flask-SQLAlchemy + PyMySQL) ----
    db.init_app(app)
    with app.app_context():
        try:
            db.session.execute(text("SELECT 1"))
        except OperationalError as exc:
            raise RuntimeError(
                "Could not connect to MySQL. Check that the server is running and that DB_HOST, DB_PORT, DB_USER, "
                "DB_PASSWORD and DB_NAME in your .env are correct, and that the database exists "
                "(run: mysql -u root -p < schema.sql).\nOriginal error: " + str(exc.orig)) from exc
        if app.config["AUTO_CREATE_TABLES"]:
            db.create_all()  # no-op for tables that already exist (e.g. created by schema.sql)

    # ---- AI service ----
    from .services.ai import AIService
    app.ai = AIService(app.config["ANTHROPIC_API_KEY"], app.config["ANTHROPIC_MODEL"])

    # ---- Blueprints ----
    from .auth import bp as auth_bp
    from .pages import bp as pages_bp
    from .resume import bp as resume_bp
    from .analyzer import bp as analyzer_bp
    from .interview import bp as interview_bp
    from .jobs import bp as jobs_bp
    from .dashboard import bp as dashboard_bp
    for b in (pages_bp, auth_bp, resume_bp, analyzer_bp, interview_bp, jobs_bp, dashboard_bp):
        app.register_blueprint(b)

    # ---- CSRF protection for all state-changing API calls ----
    @app.before_request
    def csrf_protect():
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/api/"):
            token = session.get("csrf")
            if not token or not secrets.compare_digest(token, request.headers.get("X-CSRF-Token", "")):
                return jsonify(error="Session expired. Please refresh the page and try again."), 400

    @app.context_processor
    def inject_globals():
        if "csrf" not in session:
            session["csrf"] = secrets.token_hex(16)
        return {"csrf_token": session["csrf"], "ai_enabled": app.ai.enabled}

    # ---- Error handlers (JSON for API, HTML for pages) ----
    def respond(code, msg):
        if request.path.startswith("/api/"):
            return jsonify(error=msg), code
        return render_template("error.html", code=code, message=msg), code

    def server_error(e):
        db.session.rollback()
        return respond(500, "Something went wrong on our side.")

    app.register_error_handler(404, lambda e: respond(404, "We couldn't find that page."))
    app.register_error_handler(405, lambda e: respond(405, "That action isn't allowed here."))
    app.register_error_handler(413, lambda e: respond(413, "File is too large (max 5 MB)."))
    app.register_error_handler(500, server_error)

    if seed:
        from .seed_data import seed_jobs
        with app.app_context():
            seed_jobs()
    return app
