"""Tests for Google Sign-In (OAuth 2.0 / OpenID Connect)."""

from datetime import timedelta

import pytest

from app.auth import oauth as oauth_services
from app.extensions import db
from app.users.models import AuthExchange, utcnow
from app.utils import ApiError

from tests.helpers import create_user


GOOGLE_EMAIL = "student@stu.ucc.edu.gh"


def _userinfo(email=GOOGLE_EMAIL, **overrides):
    info = {
        "email": email,
        "email_verified": True,
        "given_name": "Ama",
        "family_name": "Mensah",
    }
    info.update(overrides)
    return info


# --- Google authorization/callback gating ---------------------------------


def test_google_sign_in_disabled_when_unconfigured(client):
    resp = client.get("/api/v1/auth/google")
    assert resp.status_code == 503


def test_google_callback_disabled_when_unconfigured(client):
    resp = client.get("/api/v1/auth/google/callback")
    assert resp.status_code == 302
    assert "error=google_sign_in_disabled" in resp.headers["Location"]


def test_google_callback_invalid_token_redirects(app, client, monkeypatch):
    # Simulates Authlib raising for an invalid token / wrong audience / bad state.
    app.config["GOOGLE_CLIENT_ID"] = "test-client-id"
    app.config["GOOGLE_REDIRECT_URI"] = (
        "http://127.0.0.1:5000/api/v1/auth/google/callback"
    )

    def boom(_redirect_uri):
        raise Exception("invalid id token")

    monkeypatch.setattr(oauth_services, "google_authorize", boom)
    resp = client.get("/api/v1/auth/google/callback")
    assert resp.status_code == 302
    assert "error=google_sign_in_failed" in resp.headers["Location"]


def test_google_callback_domain_error_redirects(app, client, monkeypatch):
    app.config["GOOGLE_CLIENT_ID"] = "test-client-id"
    app.config["GOOGLE_REDIRECT_URI"] = (
        "http://127.0.0.1:5000/api/v1/auth/google/callback"
    )

    def boom(_redirect_uri):
        raise ApiError(
            "Please sign in with your official UCC email address",
            status=403,
            errors={"code": "ucc_email_required"},
        )

    monkeypatch.setattr(oauth_services, "google_authorize", boom)
    resp = client.get("/api/v1/auth/google/callback")
    assert resp.status_code == 302
    assert "error=ucc_email_required" in resp.headers["Location"]


# --- Identity validation ----------------------------------------------------


def test_authenticate_rejects_missing_email(app):
    with pytest.raises(ApiError) as exc:
        oauth_services.authenticate_google_user(_userinfo(email=""))
    assert exc.value.status == 401


def test_authenticate_rejects_unverified_email(app):
    with pytest.raises(ApiError) as exc:
        oauth_services.authenticate_google_user(_userinfo(email_verified=False))
    assert exc.value.status == 403
    assert exc.value.errors["code"] == "google_email_unverified"


def test_authenticate_rejects_disallowed_domain(app):
    app.config["ENFORCE_UCC_DOMAIN"] = True
    with pytest.raises(ApiError) as exc:
        oauth_services.authenticate_google_user(_userinfo(email="outsider@gmail.com"))
    assert exc.value.status == 403
    assert exc.value.errors["code"] == "ucc_email_required"


def test_authenticate_links_existing_account(app):
    existing = create_user("manager@stu.ucc.edu.gh", "LOCATION_MANAGER")
    user = oauth_services.authenticate_google_user(
        _userinfo(email="manager@stu.ucc.edu.gh")
    )
    assert user.id == existing.id
    assert user.role == "LOCATION_MANAGER"


def test_authenticate_creates_student_role_only(app):
    user = oauth_services.authenticate_google_user(
        _userinfo(email="new.student@stu.ucc.edu.gh")
    )
    assert user.role == "STUDENT"
    assert user.first_name == "Ama"
    assert user.last_name == "Mensah"


def test_authenticate_ignores_claimed_role(app):
    # A privileged role in the userinfo must never be trusted.
    user = oauth_services.authenticate_google_user(
        _userinfo(email="claimed@stu.ucc.edu.gh", role="SUPER_ADMIN")
    )
    assert user.role == "STUDENT"


def test_authenticate_rejects_deactivated_account(app):
    existing = create_user("inactive@stu.ucc.edu.gh", "STUDENT")
    existing.is_active = False
    db.session.commit()
    with pytest.raises(ApiError) as exc:
        oauth_services.authenticate_google_user(
            _userinfo(email="inactive@stu.ucc.edu.gh")
        )
    assert exc.value.status == 403


# --- Exchange-code flow -----------------------------------------------------


def test_exchange_successful_login(app, client):
    user = create_user(GOOGLE_EMAIL, "STUDENT")
    code = oauth_services.create_exchange_code(user)
    resp = client.post("/api/v1/auth/google/exchange", json={"code": code})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["user"]["email"] == GOOGLE_EMAIL
    assert body["data"]["access_token"]


def test_exchange_unknown_code(client):
    resp = client.post(
        "/api/v1/auth/google/exchange", json={"code": "does-not-exist"}
    )
    assert resp.status_code == 401


def test_exchange_missing_code(client):
    resp = client.post("/api/v1/auth/google/exchange", json={})
    assert resp.status_code == 422


def test_exchange_replayed_code(app, client):
    user = create_user(GOOGLE_EMAIL, "STUDENT")
    code = oauth_services.create_exchange_code(user)
    assert client.post("/api/v1/auth/google/exchange", json={"code": code}).status_code == 200
    assert client.post("/api/v1/auth/google/exchange", json={"code": code}).status_code == 401


def test_exchange_expired_code(app, client):
    user = create_user(GOOGLE_EMAIL, "STUDENT")
    old = utcnow() - timedelta(seconds=300)
    db.session.add(
        AuthExchange(code="expired-code", user_id=user.id, created_at=old)
    )
    db.session.commit()
    resp = client.post("/api/v1/auth/google/exchange", json={"code": "expired-code"})
    assert resp.status_code == 401


def test_exchange_preserves_existing_role(app, client):
    # Account linking must preserve the existing role, not create a STUDENT.
    manager = create_user("manager@stu.ucc.edu.gh", "LOCATION_MANAGER")
    code = oauth_services.create_exchange_code(manager)
    resp = client.post("/api/v1/auth/google/exchange", json={"code": code})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["user"]["role"] == "LOCATION_MANAGER"
