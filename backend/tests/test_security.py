import pytest

from app import create_app


def _clear_secrets(monkeypatch):
    # Set to empty (insecure) rather than deleting, so the test stays hermetic
    # even when a local `backend/.env` has populated the environment.
    for key in ("SECRET_KEY", "JWT_SECRET_KEY"):
        monkeypatch.setenv(key, "")


def test_production_fails_with_missing_secrets(monkeypatch):
    _clear_secrets(monkeypatch)
    with pytest.raises(RuntimeError):
        create_app("production")


def test_production_fails_with_placeholder_secrets(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "change-me-in-production")
    monkeypatch.setenv("JWT_SECRET_KEY", "change-me-in-production")
    with pytest.raises(RuntimeError):
        create_app("production")


def test_production_fails_with_short_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")
    with pytest.raises(RuntimeError):
        create_app("production")


def test_production_succeeds_with_strong_secrets(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("JWT_SECRET_KEY", "y" * 48)
    app = create_app("production")
    assert app.config["SECRET_KEY"] == "x" * 48


def test_production_register_does_not_expose_otp(monkeypatch):
    from app.config import Config

    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("JWT_SECRET_KEY", "y" * 48)
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    monkeypatch.setattr("app.auth.services.send_otp_email", lambda email, otp: None)

    app = create_app("production")

    from app.extensions import db

    with app.app_context():
        db.create_all()

    client = app.test_client()
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ama",
            "last_name": "Mensah",
            "email": "ama@stu.ucc.edu.gh",
            "password": "Password1",
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert "dev_otp" not in body
    assert body["data"]["email_verified"] is False


def test_jwt_secret_falls_back_to_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "z" * 48)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    app = create_app("production")
    assert app.config["JWT_SECRET_KEY"] == "z" * 48


def test_development_allows_default_secrets(monkeypatch):
    _clear_secrets(monkeypatch)
    app = create_app("development")
    assert app is not None
