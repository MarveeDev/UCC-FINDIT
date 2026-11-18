from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.analytics import services as analytics_services
from app.users.models import UserRole
from app.users.services import get_user_by_id
from app.utils import fail, ok

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


def _require_manager_or_admin(user):
    if user.role not in (UserRole.LOCATION_MANAGER, UserRole.SUPER_ADMIN):
        return fail("You do not have permission to view analytics", status=403)
    return None


def _parse_date(value):
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


@analytics_bp.get("/dashboard")
@jwt_required()
def dashboard():
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied

    location_id = request.args.get("location_id", type=int)
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))

    data = analytics_services.get_dashboard(user, location_id, date_from, date_to)
    return ok(data=data)


@analytics_bp.get("/analytics")
@jwt_required()
def analytics():
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied

    location_id = request.args.get("location_id", type=int)
    date_from = _parse_date(request.args.get("date_from"))
    date_to = _parse_date(request.args.get("date_to"))
    category = request.args.get("category")

    data = analytics_services.get_analytics(user, date_from, date_to, location_id, category)
    return ok(data=data)
