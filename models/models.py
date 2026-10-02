from datetime import datetime, timezone
from cryptography.fernet import Fernet
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.types import TypeDecorator, Text
from app import db, login_manager


def now():
    return datetime.now(timezone.utc)


class EncryptedText(TypeDecorator):
    """Authenticated field encryption before values reach the database driver."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return (
            Fernet(current_app.config["ENCRYPTION_KEY"]).encrypt(value.encode()).decode()
            if value is not None
            else None
        )

    def process_result_value(self, value, dialect):
        return (
            Fernet(current_app.config["ENCRYPTION_KEY"]).decrypt(value.encode()).decode()
            if value is not None
            else None
        )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(EncryptedText, nullable=False)
    last_name = db.Column(EncryptedText, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    __table_args__ = (db.CheckConstraint("role IN ('patient', 'doctor')"),)


class SymptomEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_submitted = db.Column(db.DateTime, default=now, nullable=False)
    symptoms = db.Column(EncryptedText, nullable=False)
    prediction = db.Column(EncryptedText)
    validated = db.Column(db.Boolean, default=False, nullable=False)
    note = db.Column(EncryptedText)
    patient = db.relationship("User", foreign_keys=[patient_id])


class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    symptom_entry_id = db.Column(db.Integer, db.ForeignKey("symptom_entry.id"), unique=True, nullable=False)
    date_issued = db.Column(db.DateTime, default=now, nullable=False)
    disease = db.Column(EncryptedText, nullable=False)
    description = db.Column(EncryptedText, nullable=False)
    patient = db.relationship("User", foreign_keys=[patient_id])
    doctor = db.relationship("User", foreign_keys=[doctor_id])


class AuditEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(db.String(40), nullable=False)
    record_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=now, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) if user_id.isdigit() else None
