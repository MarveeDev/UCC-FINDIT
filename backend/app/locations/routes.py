from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.locations import services as location_services
from app.users.models import UserRole
from app.users.services import serialize_user
from app.utils import fail, ok
from app.utils.decorators import role_required

locations_bp = Blueprint("locations", __name__, url_prefix="/api/v1/locations")


@locations_bp.get("")
@jwt_required()
def list_locations():
    locations = location_services.list_active_locations()
    return ok(data=[location_services.serialize_location(l) for l in locations])


@locations_bp.post("")
@role_required(UserRole.SUPER_ADMIN)
def create_location():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip() or None
    if not name:
        return fail("Location name is required", status=422)
    location = location_services.create_location(name, description)
    return ok(data=location_services.serialize_location(location), status=201)


@locations_bp.get("/<int:location_id>")
@jwt_required()
def get_location(location_id):
    location = location_services.get_location(location_id)
    return ok(data=location_services.serialize_location(location))


@locations_bp.patch("/<int:location_id>")
@role_required(UserRole.SUPER_ADMIN)
def update_location(location_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip() or None
    description = data.get("description")
    is_active = data.get("is_active")
    location = location_services.update_location(location_id, name, description, is_active)
    return ok(data=location_services.serialize_location(location))


@locations_bp.delete("/<int:location_id>")
@role_required(UserRole.SUPER_ADMIN)
def deactivate_location(location_id):
    location = location_services.update_location(location_id, is_active=False)
    return ok(
        data=location_services.serialize_location(location),
        message="Location deactivated",
    )


@locations_bp.get("/<int:location_id>/managers")
@role_required(UserRole.SUPER_ADMIN, UserRole.LOCATION_MANAGER)
def list_managers(location_id):
    location = location_services.get_location(location_id)
    managers = [
        serialize_user(m.user) for m in location.managers.all()
    ]
    return ok(data=managers)


@locations_bp.post("/<int:location_id>/managers")
@role_required(UserRole.SUPER_ADMIN)
def add_manager(location_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if user_id is None:
        return fail("user_id is required", status=422)
    location = location_services.assign_manager(location_id, int(user_id))
    return ok(
        data=location_services.serialize_location(location),
        message="Manager assigned",
        status=201,
    )


@locations_bp.delete("/<int:location_id>/managers/<int:user_id>")
@role_required(UserRole.SUPER_ADMIN)
def remove_manager(location_id, user_id):
    location_services.remove_manager(location_id, user_id)
    return ok(message="Manager unassigned")


@locations_bp.get("/<int:location_id>/staff")
@jwt_required()
def list_staff(location_id):
    user = _current_user()
    if not location_services.user_has_location_access(user, location_id):
        return fail("You do not have permission to view staff for this location", status=403)
    location = location_services.get_location(location_id)
    staff = [serialize_user(s.user) for s in location.staff_assignments.all()]
    return ok(data=staff)


@locations_bp.post("/<int:location_id>/staff")
@jwt_required()
def add_staff(location_id):
    user = _current_user()
    if not location_services.user_manages_location(user, location_id):
        return fail("You do not have permission to manage staff for this location", status=403)
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if user_id is None:
        return fail("user_id is required", status=422)
    location = location_services.assign_staff(location_id, int(user_id))
    return ok(
        data=location_services.serialize_location(location),
        message="Staff member assigned",
        status=201,
    )


@locations_bp.delete("/<int:location_id>/staff/<int:user_id>")
@jwt_required()
def remove_staff(location_id, user_id):
    user = _current_user()
    if not location_services.user_manages_location(user, location_id):
        return fail("You do not have permission to manage staff for this location", status=403)
    location_services.remove_staff(location_id, user_id)
    return ok(message="Staff member unassigned")


def _current_user():
    from app.users.services import get_user_by_id

    return get_user_by_id(int(get_jwt_identity()))
