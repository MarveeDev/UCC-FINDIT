from flask import Blueprint
from sqlalchemy import text

from app.extensions import db
from app.utils import fail, ok

health_bp = Blueprint("health", __name__, url_prefix="/api/v1/health")


@health_bp.get("")
def health():
    """Readiness check: verifies the API is reachable and the database responds."""
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        return fail("Service unavailable", status=503)
    return ok(data={"status": "ok"})
