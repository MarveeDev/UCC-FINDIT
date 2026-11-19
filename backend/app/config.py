import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _list(value, default=None):
    if value is None or str(value).strip() == "":
        return default or []
    return [item.strip() for item in str(value).split(",") if item.strip()]


# Markers that identify placeholder / development secrets that must never be
# used in production.
_INSECURE_SECRET_MARKERS = (
    "change-me",
    "change_me",
    "changeme",
    "dev-only",
    "dev_only",
    "placeholder",
    "replace-me",
    "insecure",
    "your-secret",
)


def _is_insecure_secret(value):
    """Return True when a secret is missing, too short, or a known placeholder."""
    if not value or not isinstance(value, str):
        return True
    value = value.strip()
    if len(value) < 32:
        return True
    lowered = value.lower()
    return any(marker in lowered for marker in _INSECURE_SECRET_MARKERS)


def ensure_secure_secrets(app_config):
    """Refuse to start when strong, non-default secrets are required but absent."""
    if not app_config.get("REQUIRE_STRONG_SECRETS", False):
        return
    if _is_insecure_secret(app_config.get("SECRET_KEY")):
        raise RuntimeError(
            "SECRET_KEY must be set to a strong, non-placeholder value in production"
        )
    if _is_insecure_secret(app_config.get("JWT_SECRET_KEY")):
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a strong, non-placeholder value in production"
        )


class Config:
    """Base configuration shared by every environment."""

    # When True, the application refuses to start unless SECRET_KEY and
    # JWT_SECRET_KEY are strong, non-placeholder values.
    REQUIRE_STRONG_SECRETS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-000000000000")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_HOURS", "24"))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://ucc:ucc@localhost:5432/ucc_findit"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keep pooled PostgreSQL connections healthy: managed PostgreSQL providers
    # (Render/Neon) close idle SSL connections, so verify liveness before use
    # and recycle connections before they exceed the server's idle timeout.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    CORS_ORIGINS = _list(os.getenv("CORS_ORIGINS"), ["http://localhost:5174"])

    # UCC email domain. Enforcement is OFF by default until the official
    # university email domain and delivery configuration are verified.
    ENFORCE_UCC_DOMAIN = _bool(os.getenv("ENFORCE_UCC_DOMAIN"))
    UCC_EMAIL_DOMAINS = _list(
        os.getenv("UCC_EMAIL_DOMAINS"), ["stu.ucc.edu.gh", "ucc.edu.gh"]
    )

    # Image uploads (Cloudinary object storage)
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads")),
    )
    # 6 MB request cap leaves headroom for multipart overhead; the upload route
    # enforces the stricter 5 MB per-image limit itself.
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "ucc-findit/items")

    # DB-backed rate limiting
    LOGIN_RATE_LIMIT = int(os.getenv("LOGIN_RATE_LIMIT", "10"))
    LOGIN_RATE_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "60"))
    REGISTER_RATE_LIMIT = int(os.getenv("REGISTER_RATE_LIMIT", "10"))
    REGISTER_RATE_WINDOW_SECONDS = int(os.getenv("REGISTER_RATE_WINDOW_SECONDS", "3600"))
    VERIFY_RATE_LIMIT = int(os.getenv("VERIFY_RATE_LIMIT", "5"))
    VERIFY_RATE_WINDOW_SECONDS = int(os.getenv("VERIFY_RATE_WINDOW_SECONDS", "60"))
    RESEND_RATE_LIMIT = int(os.getenv("RESEND_RATE_LIMIT", "5"))
    RESEND_RATE_WINDOW_SECONDS = int(os.getenv("RESEND_RATE_WINDOW_SECONDS", "300"))

    # Secure handover codes
    HANDOVER_CODE_EXPIRY_HOURS = int(os.getenv("HANDOVER_CODE_EXPIRY_HOURS", "24"))
    HANDOVER_CODE_MAX_ATTEMPTS = int(os.getenv("HANDOVER_CODE_MAX_ATTEMPTS", "5"))


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret-which-is-at-least-32-bytes-long"
    ENFORCE_UCC_DOMAIN = False
    LOGIN_RATE_LIMIT = 100


class ProductionConfig(Config):
    DEBUG = False
    REQUIRE_STRONG_SECRETS = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
