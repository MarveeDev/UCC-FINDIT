"""Google Sign-In (OAuth 2.0 / OpenID Connect) service.

The authorization-code flow is delegated to Authlib, which performs the
security-critical ID-token validation (signature via Google's JWKS, issuer,
audience, expiry, and nonce) using Google's OpenID Connect discovery document.

This module only adds the application-specific policy: verified-email checks,
UCC domain enforcement, safe account linking, STUDENT-only provisioning, and a
short-lived, single-use exchange code that hands the JWT back to the frontend
without ever placing it in a URL.
"""

import secrets

from authlib.integrations.flask_client import OAuth
from flask import current_app, redirect
from werkzeug.security import generate_password_hash

from app.auth.validators import email_domain_allowed, normalize_email
from app.extensions import db
from app.users.models import AuthExchange, User, UserRole, utcnow
from app.utils import ApiError

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

oauth = OAuth()


def init_oauth(app):
    """Register the Google client when credentials are configured.

    Registering only when both id and secret are present keeps the app fully
    functional (email/password auth) when Google Sign-In is not yet set up.
    """
    oauth.init_app(app)
    if app.config.get("GOOGLE_CLIENT_ID") and app.config.get("GOOGLE_CLIENT_SECRET"):
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url=GOOGLE_DISCOVERY_URL,
            client_kwargs={"scope": "openid email profile"},
        )


def google_client():
    """Return the configured Google client or raise a 503 when not set up."""
    client = oauth.create_client("google")
    if client is None:
        raise ApiError("Google sign-in is not configured", status=503)
    return client


def google_authorization_url(redirect_uri):
    """Build the Google authorization redirect (state and nonce are handled
    by Authlib and stored in the signed Flask session)."""
    return google_client().authorize_redirect(redirect_uri)


def google_authorize(redirect_uri):
    """Exchange the authorization code and resolve the verified Google user.

    Authlib validates the ID token (issuer, audience, expiry, nonce, signature)
    before returning the userinfo. Raises Authlib errors on invalid tokens.
    """
    token = google_client().authorize_access_token()
    userinfo = token.get("userinfo") or {}
    return authenticate_google_user(userinfo)


def authenticate_google_user(userinfo):
    """Validate a Google identity and resolve it to a local User.

    This is the application-specific policy layer: it never trusts the
    frontend, only the ID token claims Authlib already verified.
    """
    email = normalize_email(userinfo.get("email") or "")
    if not email:
        raise ApiError(
            "Google account did not return a valid email address", status=401
        )
    if userinfo.get("email_verified") is not True:
        raise ApiError(
            "This Google account's email is not verified. Verify it and try again.",
            status=403,
            errors={"code": "google_email_unverified"},
        )
    if current_app.config.get("ENFORCE_UCC_DOMAIN") and not email_domain_allowed(email):
        raise ApiError(
            "Please sign in with your official UCC email address",
            status=403,
            errors={"code": "ucc_email_required"},
        )

    user = User.query.filter_by(email=email).first()
    if user is None:
        user = create_google_student(email, userinfo)
    if not user.is_active:
        raise ApiError("This account has been deactivated", status=403)
    return user


def create_google_student(email, userinfo):
    """Provision a new STUDENT account for a verified Google identity.

    The password hash is a random, unknowable value, so the account can only be
    used via Google sign-in. Privileged roles are never assigned here.
    """
    first_name = (userinfo.get("given_name") or "").strip()
    last_name = (userinfo.get("family_name") or "").strip()
    if not first_name:
        first_name = (userinfo.get("name") or email.split("@")[0]).strip()
    if not last_name:
        last_name = "User"

    user = User(
        first_name=first_name[:80],
        last_name=last_name[:80],
        email=email,
        password_hash=generate_password_hash(secrets.token_urlsafe(32)),
        role=UserRole.STUDENT,
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_exchange_code(user):
    """Create a single-use, short-lived exchange code bound to the user."""
    code = secrets.token_urlsafe(48)
    db.session.add(AuthExchange(code=code, user_id=user.id))
    db.session.commit()
    return code


def consume_exchange_code(code):
    """Atomically redeem a single-use exchange code and return the User."""
    exchange = db.session.get(AuthExchange, code)
    if exchange is None:
        raise ApiError("Invalid or expired sign-in code", status=401)

    ttl = current_app.config.get("GOOGLE_EXCHANGE_TTL_SECONDS", 120)
    age = (utcnow() - exchange.created_at).total_seconds()
    if age > ttl:
        raise ApiError("Sign-in code has expired", status=401)

    user_id = exchange.user_id
    claimed = AuthExchange.query.filter(
        AuthExchange.code == code, AuthExchange.consumed_at.is_(None)
    ).update({"consumed_at": utcnow()}, synchronize_session=False)
    db.session.commit()
    if not claimed:
        raise ApiError("Sign-in code has already been used", status=401)

    user = db.session.get(User, user_id)
    if user is None or not user.is_active:
        raise ApiError("This account is not available", status=403)
    return user


def redirect_with_code(code):
    """Redirect the browser back to the frontend with the exchange code."""
    frontend = current_app.config.get("FRONTEND_URL", "").rstrip("/")
    return redirect(f"{frontend}/auth/google/callback?code={code}")


def redirect_with_error(error_key):
    """Redirect the browser back to the frontend login page with an error."""
    frontend = current_app.config.get("FRONTEND_URL", "").rstrip("/")
    return redirect(f"{frontend}/login?error={error_key}")
