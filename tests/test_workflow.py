from io import BytesIO
from sqlalchemy import text
from tests.conftest import sign_in
from app import db
from models.models import User, SymptomEntry, Prescription, AuditEvent


def test_complete_review_and_owned_download(client, app):
    assert sign_in(client).status_code == 302
    assert client.get("/patient/dashboard").status_code == 200
    assert client.post("/patient/submit", data={"symptoms": ["itching", "skin_rash"]}).status_code == 302
    assert client.get("/doctor/dashboard").status_code == 403
    with app.app_context():
        entry = SymptomEntry.query.one()
        entry_id = entry.id
        raw = db.session.execute(text("SELECT symptoms FROM symptom_entry")).scalar()
        assert "itching" not in raw
        assert entry.symptoms == "itching,skin_rash"
    client.post("/logout")
    sign_in(client, "doctor@example.test")
    assert client.get("/doctor/dashboard").status_code == 200
    assert client.get(f"/doctor/validate/{entry_id}").status_code == 200
    payload = {"assessment": "Demo assessment", "note": "Fictional follow-up notes for the portfolio."}
    assert client.post(f"/doctor/validate/{entry_id}", data=payload).status_code == 302
    assert client.post(f"/doctor/validate/{entry_id}", data=payload).status_code == 409
    with app.app_context():
        assert Prescription.query.count() == 1
        assert db.session.get(SymptomEntry, entry_id).validated
        record_id = Prescription.query.one().id
        assert AuditEvent.query.filter_by(action="review").count() == 1
    client.post("/logout")
    sign_in(client, "other@example.test")
    assert client.get(f"/patient/download/{record_id}").status_code == 404
    assert b"Demo assessment" not in client.get("/patient/dashboard").data
    client.post("/logout")
    sign_in(client)
    response = client.get(f"/patient/download/{record_id}")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF")
    assert response.headers["Cache-Control"] == "no-store"
    from pypdf import PdfReader

    assert "Demo assessment" in PdfReader(BytesIO(response.data)).pages[0].extract_text()


def test_role_escalation_is_ignored(client, app):
    result = client.post(
        "/register",
        data={
            "first_name": "Test",
            "last_name": "Person",
            "email": "NEW@example.test",
            "password": "long-enough-password",
            "role": "doctor",
        },
    )
    assert result.status_code == 302
    with app.app_context():
        user = User.query.filter_by(email="new@example.test").one()
        assert user.role == "patient"
        assert user.password != "long-enough-password"


def test_invalid_and_empty_symptoms_rejected(client):
    sign_in(client)
    for payload in ({}, {"symptoms": ["unknown"]}, {"symptoms": ["itching", "invalid"]}):
        assert client.post("/patient/submit", data=payload).status_code == 400


def test_unauthenticated_routes(client):
    for path in ("/patient/dashboard", "/doctor/dashboard", "/patient/download/1"):
        assert client.get(path).status_code == 302
    assert client.get("/logout").status_code == 405


def test_csrf_and_headers(app):
    app.config["WTF_CSRF_ENABLED"] = True
    client = app.test_client()
    assert client.post("/login", data={"email": "a", "password": "b"}).status_code == 400
    response = client.get("/login")
    assert b"csrf_token" in response.data
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_html_in_notes_is_escaped(client, app):
    sign_in(client)
    client.post("/patient/submit", data={"symptoms": ["itching"]})
    client.post("/logout")
    sign_in(client, "doctor@example.test")
    client.post(
        "/doctor/validate/1",
        data={"assessment": "<script>alert(1)</script>", "note": "Testing HTML escaping for patient notes."},
    )
    client.post("/logout")
    sign_in(client)
    response = client.get("/patient/dashboard")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_failed_review_does_not_close_entry(client, app):
    sign_in(client)
    client.post("/patient/submit", data={"symptoms": ["itching"]})
    client.post("/logout")
    sign_in(client, "doctor@example.test")
    assert client.post("/doctor/validate/1", data={"assessment": "x", "note": ""}).status_code == 400
    with app.app_context():
        assert not db.session.get(SymptomEntry, 1).validated
        assert Prescription.query.count() == 0


def test_encrypted_values_are_randomized_and_tampering_fails(app):
    from cryptography.fernet import InvalidToken
    from models.models import EncryptedText

    with app.app_context():
        field = EncryptedText()
        first = field.process_bind_param("sensitive note", None)
        second = field.process_bind_param("sensitive note", None)
        assert first != second
        assert field.process_result_value(first, None) == "sensitive note"
        import pytest

        with pytest.raises(InvalidToken):
            field.process_result_value(first[:-4] + "AAAA", None)


def test_authenticated_not_found_page(client):
    sign_in(client)
    assert client.get("/no-such-page").status_code == 404


def test_production_requires_secrets(monkeypatch):
    import pytest
    from app import create_app

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError):
        create_app()


def test_login_throttling():
    from app import create_app
    from cryptography.fernet import Fernet

    limited_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "ENCRYPTION_KEY": Fernet.generate_key(),
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": True,
        }
    )
    with limited_app.app_context():
        db.create_all()
    limited_client = limited_app.test_client()
    for _ in range(5):
        assert (
            limited_client.post(
                "/login", data={"email": "missing@example.test", "password": "incorrect"}
            ).status_code
            == 401
        )
    assert (
        limited_client.post(
            "/login", data={"email": "missing@example.test", "password": "incorrect"}
        ).status_code
        == 429
    )
