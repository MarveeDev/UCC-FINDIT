from flask import Blueprint, current_app, request
from flask_jwt_extended import jwt_required

from app.auth import oauth as oauth_services
from app.auth import services as auth_services
from app.auth import validators
from app.security.services import client_ip, enforce_rate_limit
from app.users.services import serialize_user
from app.utils import ApiError, fail, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    errors, first_name, last_name, email, password = validators.validate_registration(data)
    if errors:
        return fail("Validation failed", status=422, errors=errors)

    enforce_rate_limit(
        "register",
        client_ip(),
        current_app.config["REGISTER_RATE_LIMIT"],
        current_app.config["REGISTER_RATE_WINDOW_SECONDS"],
    )

    result = auth_services.register_user(first_name, last_name, email, password)
    return ok(data=result["user"], message=result["message"], status=201)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return fail("Email and password are required", status=422)

    enforce_rate_limit(
        "login",
        client_ip(),
        current_app.config["LOGIN_RATE_LIMIT"],
        current_app.config["LOGIN_RATE_WINDOW_SECONDS"],
    )

    result = auth_services.login(email, password)
    return ok(data=result)


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # JWT authentication is stateless; the client discards its token on logout.
    return ok(message="Logged out successfully")


@auth_bp.get("/google")
def google_login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return fail("Google sign-in is not configured", status=503)
    return oauth_services.google_authorization_url(
        current_app.config["GOOGLE_REDIRECT_URI"]
    )


@auth_bp.get("/google/callback")
def google_callback():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        return oauth_services.redirect_with_error("google_sign_in_disabled")
    try:
        user = oauth_services.google_authorize(
            current_app.config["GOOGLE_REDIRECT_URI"]
        )
    except ApiError as exc:
        error_key = (exc.errors or {}).get("code") or "google_sign_in_failed"
        return oauth_services.redirect_with_error(error_key)
    except Exception:
        # Authlib raises its own errors for invalid state/tokens; never surface
        # those details to the client and never leak secrets.
        current_app.logger.exception("Google OAuth callback failed")
        return oauth_services.redirect_with_error("google_sign_in_failed")
    code = oauth_services.create_exchange_code(user)
    return oauth_services.redirect_with_code(code)


@auth_bp.post("/google/exchange")
def google_exchange():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    if not code:
        return fail("A sign-in code is required", status=422)
    try:
        user = oauth_services.consume_exchange_code(code)
    except ApiError as exc:
        return fail(exc.message, status=exc.status)
    return ok(
        data={
            "user": serialize_user(user),
            "access_token": auth_services.create_token(user),
        }
    )
