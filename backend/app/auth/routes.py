from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.auth import services as auth_services
from app.auth import validators
from app.utils import fail, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    errors, first_name, last_name, email, password = validators.validate_registration(data)
    if errors:
        return fail("Validation failed", status=422, errors=errors)

    result = auth_services.register_user(first_name, last_name, email, password)
    return ok(
        data=result["user"],
        message=result["message"],
        status=201,
        **result.get("extra", {}),
    )


@auth_bp.post("/verify-email")
def verify_email():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()
    if not email or not otp:
        return fail("Email and verification code are required", status=422)

    result = auth_services.verify_email(email, otp)
    return ok(data=result, message=result["message"])


@auth_bp.post("/resend-otp")
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return fail("Email is required", status=422)

    result = auth_services.resend_otp(email)
    return ok(message=result["message"], **result.get("extra", {}))


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return fail("Email and password are required", status=422)

    result = auth_services.login(email, password)
    return ok(data=result)


@auth_bp.post("/logout")
@jwt_required()
def logout():
    # JWT authentication is stateless; the client discards its token on logout.
    return ok(message="Logged out successfully")
