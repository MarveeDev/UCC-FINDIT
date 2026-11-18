import logging
import secrets
from datetime import timedelta

from flask import current_app
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.users.models import OtpVerification, User, utcnow
from app.users.services import serialize_user
from app.utils import ApiError
from app.utils.mail import EmailDeliveryError, send_otp_email

logger = logging.getLogger(__name__)


def register_user(first_name, last_name, email, password):
    if get_user(email):
        raise ApiError("An account with this email already exists", status=409)

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.flush()

    try:
        otp = issue_email_otp(user)
    except EmailDeliveryError:
        db.session.rollback()
        raise ApiError(
            "We couldn't send your verification code. Please try again.",
            status=503,
        )

    extra = {}
    if current_app.config.get("EXPOSE_OTP_IN_RESPONSE"):
        extra["dev_otp"] = otp

    return {
        "user": serialize_user(user),
        "message": "Account created. Verify your email with the issued code.",
        "extra": extra,
    }


def get_user(email):
    return User.query.filter_by(email=email).first()


def issue_email_otp(user):
    otp = f"{secrets.randbelow(10 ** 6):06d}"
    expires_at = utcnow() + timedelta(
        minutes=current_app.config["OTP_EXPIRY_MINUTES"]
    )
    record = OtpVerification(
        user_id=user.id,
        otp_hash=generate_password_hash(otp),
        purpose="email_verification",
        attempts=0,
        expires_at=expires_at,
        last_sent_at=utcnow(),
    )
    db.session.add(record)
    _deliver_otp(user.email, otp)
    db.session.commit()
    return otp


def _deliver_otp(email, otp):
    """Deliver the verification code through the configured channel.

    Development and testing log the code to the console (and the caller returns
    it as ``dev_otp``). Production delivers it via the Resend email API and
    never logs or returns the plaintext code. Raises EmailDeliveryError when
    production delivery fails.
    """
    if current_app.config.get("EXPOSE_OTP_IN_RESPONSE"):
        logger.info("[DEV OTP] verification code for %s: %s", email, otp)
        return
    send_otp_email(email, otp)


def _latest_otp_record(email):
    user = get_user(email)
    if user is None:
        raise ApiError("No account found for this email", status=404)
    record = (
        OtpVerification.query.filter_by(user_id=user.id, purpose="email_verification")
        .order_by(OtpVerification.created_at.desc())
        .first()
    )
    return user, record


def verify_email(email, otp):
    user, record = _latest_otp_record(email)
    if record is None:
        raise ApiError("No verification code found. Request a new one.", status=400)
    if record.expires_at < utcnow():
        raise ApiError("This verification code has expired. Request a new one.", status=400)
    if record.attempts >= current_app.config["OTP_MAX_ATTEMPTS"]:
        raise ApiError("Too many attempts. Request a new verification code.", status=429)
    if not check_password_hash(record.otp_hash, otp):
        record.attempts += 1
        db.session.commit()
        raise ApiError("Invalid verification code.", status=400)

    user.email_verified = True
    db.session.delete(record)
    db.session.commit()

    return {
        "user": serialize_user(user),
        "access_token": _create_token(user),
        "message": "Email verified successfully",
    }


def resend_otp(email):
    user, record = _latest_otp_record(email)
    if user.email_verified:
        raise ApiError("Email is already verified", status=400)

    if record is not None:
        cooldown = timedelta(seconds=current_app.config["OTP_RESEND_COOLDOWN_SECONDS"])
        elapsed = utcnow() - record.last_sent_at
        if elapsed < cooldown:
            remaining = int((cooldown - elapsed).total_seconds())
            raise ApiError(
                "Please wait before requesting another code",
                status=429,
                errors={"retry_after": remaining},
            )
        db.session.delete(record)
        db.session.commit()

    try:
        otp = issue_email_otp(user)
    except EmailDeliveryError:
        db.session.rollback()
        raise ApiError(
            "We couldn't send your verification code. Please try again.",
            status=503,
        )

    extra = {}
    if current_app.config.get("EXPOSE_OTP_IN_RESPONSE"):
        extra["dev_otp"] = otp
    return {"message": "A new verification code has been sent.", "extra": extra}


def login(email, password):
    user = get_user(email)
    if user is None or not check_password_hash(user.password_hash, password):
        raise ApiError("Invalid email or password", status=401)
    if not user.is_active:
        raise ApiError("This account has been deactivated", status=403)
    return {"user": serialize_user(user), "access_token": _create_token(user)}


def _create_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email},
    )
