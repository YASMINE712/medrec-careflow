import pytest
from cryptography.fernet import Fernet
from werkzeug.security import generate_password_hash
from app import create_app, db
from models.models import User


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-secret",
            "ENCRYPTION_KEY": Fernet.generate_key(),
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    with app.app_context():
        db.create_all()
        for email, role in [
            ("patient@example.test", "patient"),
            ("other@example.test", "patient"),
            ("doctor@example.test", "doctor"),
        ]:
            db.session.add(
                User(
                    first_name="Fictional",
                    last_name="Person",
                    email=email,
                    role=role,
                    password=generate_password_hash("test-passphrase-123"),
                )
            )
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def sign_in(client, email="patient@example.test"):
    return client.post("/login", data={"email": email, "password": "test-passphrase-123"})
