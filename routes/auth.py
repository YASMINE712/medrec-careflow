import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from app import db, limiter
from models.models import User, AuditEvent

auth_bp = Blueprint("auth", __name__)
DUMMY_HASH = generate_password_hash("dummy-password-for-timing-only")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def register():
    if request.method == "POST":
        first, last = (request.form.get(k, "").strip() for k in ("first_name", "last_name"))
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not (
            1 <= len(first) <= 50
            and 1 <= len(last) <= 50
            and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
            and len(email) <= 254
            and 12 <= len(password) <= 128
        ):
            flash("Check your details. Passwords must have 12-128 characters.")
            return render_template("register.html"), 400
        db.session.add(
            User(
                first_name=first,
                last_name=last,
                email=email,
                password=generate_password_hash(password),
                role="patient",
            )
        )
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        flash("If registration was successful, you can now sign in.")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        valid = check_password_hash(user.password if user else DUMMY_HASH, request.form.get("password", ""))
        if not user or not valid:
            flash("Invalid email or password.")
            return render_template("login.html"), 401
        session.clear()
        session.permanent = True
        login_user(user)
        db.session.add(AuditEvent(actor_id=user.id, action="login"))
        db.session.commit()
        return redirect(url_for(f"{user.role}.dashboard"))
    return render_template("login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
