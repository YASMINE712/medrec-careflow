from datetime import timedelta
from pathlib import Path
import os
import secrets
import click
from cryptography.fernet import Fernet
from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(exist_ok=True)
    production = os.getenv("APP_ENV") == "production"
    secret, encryption = os.getenv("SECRET_KEY"), os.getenv("ENCRYPTION_KEY")
    if not test_config:
        if production and (not secret or not encryption):
            raise RuntimeError("Production requires SECRET_KEY and ENCRYPTION_KEY.")
        if not production:
            keyfile = Path(app.instance_path) / "local.keys"
            if not keyfile.exists():
                keyfile.write_text(secrets.token_hex(32) + chr(10) + Fernet.generate_key().decode())
            local_secret, local_encryption = keyfile.read_text().splitlines()
            secret, encryption = secret or local_secret, encryption or local_encryption
    app.config.update(
        SECRET_KEY=secret,
        ENCRYPTION_KEY=encryption,
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///medrec.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=64 * 1024,
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
    if test_config:
        app.config.update(test_config)
    Fernet(app.config["ENCRYPTION_KEY"])
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"
    from routes.auth import auth_bp
    from routes.patient import patient_bp
    from routes.doctor import doctor_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for(f"{current_user.role}.dashboard"))
        return redirect(url_for("auth.login"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.after_request
    def headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        if production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    for code in (400, 403, 404, 409, 413, 429, 500):
        app.register_error_handler(
            code, lambda error: (render_template("error.html", code=error.code), error.code)
        )

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("create-doctor")
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_doctor(email, password):
        from models.models import User
        from werkzeug.security import generate_password_hash

        if not 12 <= len(password) <= 128 or "@" not in email:
            raise click.ClickException("Use a valid email and a 12-128 character password.")
        if User.query.filter_by(email=email.strip().lower()).first():
            raise click.ClickException("Account already exists.")
        db.session.add(
            User(
                first_name="Demo",
                last_name="Clinician",
                email=email.strip().lower(),
                password=generate_password_hash(password),
                role="doctor",
            )
        )
        db.session.commit()
        click.echo("Clinician created.")

    return app
