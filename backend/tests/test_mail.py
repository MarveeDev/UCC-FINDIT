from unittest.mock import patch

import pytest

from app import create_app
from app.utils.mail import EmailDeliveryError, send_otp_email


def _production_app(monkeypatch):
    from app.config import Config

    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("JWT_SECRET_KEY", "y" * 48)
    monkeypatch.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app = create_app("production")
    app.config["RESEND_API_KEY"] = "re_test_key"
    app.config["MAIL_FROM"] = "UCC FINDIT <noreply@uccfindit.app>"
    app.config["FRONTEND_URL"] = "https://app.uccfindit.example"
    return app


def _seed_db(app):
    from app.extensions import db

    with app.app_context():
        db.create_all()


def test_send_otp_email_posts_branded_payload(monkeypatch):
    app = _production_app(monkeypatch)
    with patch("app.utils.mail.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        with app.app_context():
            send_otp_email("ama@stu.ucc.edu.gh", "123456")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.resend.com/emails"
        assert kwargs["headers"]["Authorization"] == "Bearer re_test_key"
        payload = kwargs["json"]
        assert payload["from"] == "UCC FINDIT <noreply@uccfindit.app>"
        assert payload["to"] == ["ama@stu.ucc.edu.gh"]
        assert "123456" in payload["html"]
        assert "123456" in payload["text"]
        assert "UCC FINDIT" in payload["html"]
        assert "expires in 5 minutes" in payload["text"]
        assert "https://app.uccfindit.example/verify-email" in payload["text"]


def test_send_otp_email_requires_config(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "x" * 48)
    monkeypatch.setenv("JWT_SECRET_KEY", "y" * 48)
    app = create_app("production")
    with app.app_context():
        with pytest.raises(EmailDeliveryError):
            send_otp_email("ama@stu.ucc.edu.gh", "123456")


def test_send_otp_email_raises_on_api_rejection(monkeypatch):
    app = _production_app(monkeypatch)
    with patch("app.utils.mail.requests.post") as mock_post:
        mock_post.return_value.status_code = 422
        with app.app_context():
            with pytest.raises(EmailDeliveryError):
                send_otp_email("ama@stu.ucc.edu.gh", "123456")


def test_send_otp_email_raises_on_network_error(monkeypatch):
    import requests

    app = _production_app(monkeypatch)
    with patch(
        "app.utils.mail.requests.post", side_effect=requests.ConnectionError("boom")
    ):
        with app.app_context():
            with pytest.raises(EmailDeliveryError):
                send_otp_email("ama@stu.ucc.edu.gh", "123456")


def test_production_register_sends_email_and_hides_otp(monkeypatch):
    app = _production_app(monkeypatch)
    _seed_db(app)

    sent = []
    with patch(
        "app.auth.services.send_otp_email",
        side_effect=lambda email, otp: sent.append((email, otp)),
    ):
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
    assert len(sent) == 1
    assert sent[0][0] == "ama@stu.ucc.edu.gh"
    assert len(sent[0][1]) == 6


def test_production_register_rolls_back_on_delivery_failure(monkeypatch):
    app = _production_app(monkeypatch)
    _seed_db(app)

    with patch(
        "app.auth.services.send_otp_email", side_effect=EmailDeliveryError("boom")
    ):
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

    assert resp.status_code == 503

    from app.users.models import User

    with app.app_context():
        assert User.query.count() == 0


def test_resend_otp_sends_email_in_production(monkeypatch):
    app = _production_app(monkeypatch)
    app.config["OTP_RESEND_COOLDOWN_SECONDS"] = 0
    _seed_db(app)

    sent = []
    with patch(
        "app.auth.services.send_otp_email",
        side_effect=lambda email, otp: sent.append((email, otp)),
    ):
        client = app.test_client()
        client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Ama",
                "last_name": "Mensah",
                "email": "ama@stu.ucc.edu.gh",
                "password": "Password1",
            },
        )
        resp = client.post(
            "/api/v1/auth/resend-otp", json={"email": "ama@stu.ucc.edu.gh"}
        )

    assert resp.status_code == 200
    assert "dev_otp" not in resp.get_json()
    assert len(sent) == 2
