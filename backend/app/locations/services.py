from app.extensions import db
from app.locations.models import CampusLocation, LocationManager, StaffAssignment
from app.users.models import User, UserRole
from app.utils import ApiError


def serialize_location(location, include_assignments=False):
    data = {
        "id": location.id,
        "name": location.name,
        "description": location.description,
        "is_active": location.is_active,
        "created_at": location.created_at.isoformat() if location.created_at else None,
    }
    if include_assignments:
        data["manager_ids"] = [m.user_id for m in location.managers.all()]
        data["staff_ids"] = [s.user_id for s in location.staff_assignments.all()]
    return data


def list_active_locations():
    return (
        CampusLocation.query.filter_by(is_active=True)
        .order_by(CampusLocation.name)
        .all()
    )


def get_location(location_id):
    location = db.session.get(CampusLocation, location_id)
    if location is None:
        raise ApiError("Location not found", status=404)
    return location


def create_location(name, description=None):
    if CampusLocation.query.filter_by(name=name).first():
        raise ApiError("A location with this name already exists", status=409)
    location = CampusLocation(name=name, description=description)
    db.session.add(location)
    db.session.commit()
    return location


def update_location(location_id, name=None, description=None, is_active=None):
    location = get_location(location_id)
    if name is not None and name != location.name:
        if CampusLocation.query.filter_by(name=name).first():
            raise ApiError("A location with this name already exists", status=409)
        location.name = name
    if description is not None:
        location.description = description
    if is_active is not None:
        location.is_active = bool(is_active)
    db.session.commit()
    return location


def assign_manager(location_id, user_id):
    location = get_location(location_id)
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("User not found", status=404)
    existing = LocationManager.query.filter_by(
        user_id=user_id, location_id=location_id
    ).first()
    if existing:
        raise ApiError("This manager is already assigned to this location", status=409)
    db.session.add(LocationManager(user_id=user_id, location_id=location_id))
    db.session.commit()
    return location


def remove_manager(location_id, user_id):
    get_location(location_id)
    assignment = LocationManager.query.filter_by(
        user_id=user_id, location_id=location_id
    ).first()
    if assignment is None:
        raise ApiError("Manager assignment not found", status=404)
    db.session.delete(assignment)
    db.session.commit()


def assign_staff(location_id, user_id):
    location = get_location(location_id)
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("User not found", status=404)
    existing = StaffAssignment.query.filter_by(
        user_id=user_id, location_id=location_id
    ).first()
    if existing:
        raise ApiError("This staff member is already assigned to this location", status=409)
    db.session.add(StaffAssignment(user_id=user_id, location_id=location_id))
    db.session.commit()
    return location


def remove_staff(location_id, user_id):
    get_location(location_id)
    assignment = StaffAssignment.query.filter_by(
        user_id=user_id, location_id=location_id
    ).first()
    if assignment is None:
        raise ApiError("Staff assignment not found", status=404)
    db.session.delete(assignment)
    db.session.commit()


def user_manages_location(user, location_id):
    """True for super admins and for managers assigned to the location."""
    if user.role == UserRole.SUPER_ADMIN:
        return True
    if user.role != UserRole.LOCATION_MANAGER:
        return False
    return (
        LocationManager.query.filter_by(user_id=user.id, location_id=location_id).first()
        is not None
    )


def user_has_location_access(user, location_id):
    """True for super admins, assigned managers, and assigned staff."""
    if user.role == UserRole.SUPER_ADMIN:
        return True
    if user.role == UserRole.LOCATION_MANAGER:
        return user_manages_location(user, location_id)
    if user.role == UserRole.LOCATION_STAFF:
        return (
            StaffAssignment.query.filter_by(
                user_id=user.id, location_id=location_id
            ).first()
            is not None
        )
    return False


def responsible_manager_ids(location_id):
    """Return the user ids of managers assigned to a location (may be empty)."""
    return [
        m.user_id
        for m in LocationManager.query.filter_by(location_id=location_id).all()
    ]
