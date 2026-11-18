from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.audit.services import STAFF_ASSIGNED, STAFF_REMOVED, record_audit
from app.staff import services as staff_services
from app.users.models import UserRole
from app.users.services import get_user_by_id, serialize_user
from app.utils import fail, ok

staff_bp = Blueprint("staff", __name__, url_prefix="/api/v1/staff")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


def _require_manager_or_admin(user):
    if user.role not in (UserRole.LOCATION_MANAGER, UserRole.SUPER_ADMIN):
        return fail("You do not have permission to manage staff", status=403)
    return None


@staff_bp.get("")
@jwt_required()
def list_staff():
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied
    return ok(data=staff_services.list_staff(user))


@staff_bp.post("")
@jwt_required()
def create_staff():
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied

    data = request.get_json(silent=True) or {}
    staff = staff_services.create_staff(
        user,
        data.get("first_name"),
        data.get("last_name"),
        data.get("email"),
        data.get("password"),
        data.get("location_id"),
    )
    record_audit(
        user.id,
        STAFF_ASSIGNED,
        "user",
        staff.id,
        data.get("location_id"),
        metadata={"email": staff.email},
    )
    return ok(data=serialize_user(staff), message="Staff created and assigned", status=201)


@staff_bp.delete("/<int:user_id>/assignments/<int:location_id>")
@jwt_required()
def remove_staff_assignment(user_id, location_id):
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied

    staff_services.remove_staff_assignment(user, user_id, location_id)
    record_audit(user.id, STAFF_REMOVED, "user", user_id, location_id)
    return ok(message="Staff assignment removed")


@staff_bp.get("/<int:user_id>/activity")
@jwt_required()
def staff_activity(user_id):
    user = _current_user()
    denied = _require_manager_or_admin(user)
    if denied:
        return denied
    return ok(data=staff_services.staff_activity(user, user_id))


@staff_bp.get("/locations/mine")
@jwt_required()
def my_locations():
    user = _current_user()
    locations = staff_services.manager_locations(user)
    from app.locations.services import serialize_location

    return ok(data=[serialize_location(loc) for loc in locations])
