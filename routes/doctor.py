from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models.models import SymptomEntry, Prescription, AuditEvent
from app import db

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")


@doctor_bp.before_request
@login_required
def authorize():
    if current_user.role != "doctor":
        abort(403)


@doctor_bp.get("/dashboard")
def dashboard():
    entries = SymptomEntry.query.filter_by(validated=False).order_by(SymptomEntry.date_submitted).all()
    return render_template("doctor_dashboard.html", entries=entries)


@doctor_bp.route("/validate/<int:entry_id>", methods=["GET", "POST"])
def validate_entry(entry_id):
    entry = db.get_or_404(SymptomEntry, entry_id)
    if entry.validated:
        abort(409)
    if request.method == "POST":
        assessment = request.form.get("assessment", "").strip()
        note = request.form.get("note", "").strip()
        if not 3 <= len(assessment) <= 200 or not 10 <= len(note) <= 5000:
            flash("Enter an assessment (3-200 characters) and care notes (10-5000 characters).")
            return render_template("validate_entry.html", entry=entry), 400
        entry.validated = True
        entry.note = note
        db.session.add(
            Prescription(
                doctor_id=current_user.id,
                patient_id=entry.patient_id,
                symptom_entry_id=entry.id,
                disease=assessment,
                description=note,
            )
        )
        db.session.add(AuditEvent(actor_id=current_user.id, action="review", record_id=entry.id))
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(409)
        flash("Care summary saved and shared with the patient.")
        return redirect(url_for("doctor.dashboard"))
    db.session.add(AuditEvent(actor_id=current_user.id, action="view", record_id=entry.id))
    db.session.commit()
    return render_template("validate_entry.html", entry=entry)
