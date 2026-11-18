import pytest

from app import create_app


def test_health_endpoint(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_production_email_requires_smtp(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("JWT_SECRET_KEY", "y" * 48)
    monkeypatch.setenv("SMTP_HOST", "")

    from app.utils.mail import send_otp_email

    app = create_app("production")
    with app.app_context():
        with pytest.raises(RuntimeError):
            send_otp_email("test@example.com", "123456")


def test_register_fails_safely_without_email_config(client, app):
    app.config["MAIL_DEBUG"] = False
    app.config["SMTP_HOST"] = ""

    resp = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ama",
            "last_name": "Mensah",
            "email": "ama@stu.ucc.edu.gh",
            "password": "Password1",
        },
    )
    assert resp.status_code == 503

    from app.users.models import User

    with app.app_context():
        assert User.query.count() == 0
