from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from app import db
from models.models import SymptomEntry, Prescription, AuditEvent
from ml.ml_model import predict, symptom_names
from utils.pdf_generator import generate_pdf

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")


@patient_bp.before_request
@login_required
def authorize():
    if current_user.role != "patient":
        abort(403)


@patient_bp.route("/submit", methods=["GET", "POST"])
def submit_symptoms():
    names = symptom_names()
    if request.method == "POST":
        symptoms = list(dict.fromkeys(request.form.getlist("symptoms")))
        if not 1 <= len(symptoms) <= 15 or not set(symptoms) <= set(names):
            flash("Select between 1 and 15 symptoms from the list.")
            return render_template("submit_symptoms.html", all_symptoms=names), 400
        result = predict(symptoms)
        entry = SymptomEntry(
            patient_id=current_user.id, symptoms=",".join(symptoms), prediction=result["disease"]
        )
        db.session.add(entry)
        db.session.flush()
        db.session.add(AuditEvent(actor_id=current_user.id, action="submit", record_id=entry.id))
        db.session.commit()
        flash("Your check-in is ready for clinician review.")
        return redirect(url_for("patient.dashboard"))
    return render_template("submit_symptoms.html", all_symptoms=names)


@patient_bp.get("/dashboard")
def dashboard():
    entries = (
        SymptomEntry.query.filter_by(patient_id=current_user.id)
        .order_by(SymptomEntry.date_submitted.desc())
        .all()
    )
    prescriptions = (
        Prescription.query.filter_by(patient_id=current_user.id)
        .order_by(Prescription.date_issued.desc())
        .all()
    )
    return render_template("patient_dashboard.html", entries=entries, prescriptions=prescriptions)


@patient_bp.get("/download/<int:prescription_id>")
def download_pdf(prescription_id):
    prescription = Prescription.query.filter_by(id=prescription_id, patient_id=current_user.id).first_or_404()
    output = generate_pdf(prescription)
    db.session.add(AuditEvent(actor_id=current_user.id, action="download", record_id=prescription.id))
    db.session.commit()
    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"care-summary-{prescription.id}.pdf",
    )
