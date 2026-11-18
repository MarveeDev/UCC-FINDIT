from sqlalchemy import func

from app.extensions import db
from app.inspections.models import Inspection
from app.items.models import ItemReport, ReportType
from app.locations.models import CampusLocation, LocationManager, StaffAssignment
from app.locations.services import (
    assign_staff,
    remove_staff,
    serialize_location,
    user_manages_location,
)
from app.users.models import User, UserRole
from app.users.services import create_user, serialize_user
from app.utils import ApiError


def _scope_location_ids(user):
    if user.role == UserRole.SUPER_ADMIN:
        return [loc.id for loc in CampusLocation.query.with_entities(CampusLocation.id).all()]
    if user.role == UserRole.LOCATION_MANAGER:
        return [m.location_id for m in LocationManager.query.filter_by(user_id=user.id).all()]
    if user.role == UserRole.LOCATION_STAFF:
        return [s.location_id for s in StaffAssignment.query.filter_by(user_id=user.id).all()]
    return []


def manager_locations(user):
    ids = _scope_location_ids(user)
    return CampusLocation.query.filter(CampusLocation.id.in_(ids)).order_by(
        CampusLocation.name
    ).all()


def create_staff(actor, first_name, last_name, email, password, location_id):
    if not user_manages_location(actor, location_id):
        raise ApiError("You do not manage this location", status=403)
    user = create_user(first_name, last_name, email, password, UserRole.LOCATION_STAFF)
    assign_staff(location_id, user.id)
    return user


def remove_staff_assignment(actor, user_id, location_id):
    if not user_manages_location(actor, location_id):
        raise ApiError("You do not manage this location", status=403)
    remove_staff(location_id, user_id)


def list_staff(user):
    location_ids = _scope_location_ids(user)
    if user.role not in (UserRole.LOCATION_MANAGER, UserRole.SUPER_ADMIN):
        raise ApiError("You do not have permission to view staff", status=403)
    if not location_ids:
        return []

    staff_user_ids = [
        row[0]
        for row in db.session.query(StaffAssignment.user_id)
        .filter(StaffAssignment.location_id.in_(location_ids))
        .distinct()
        .all()
    ]
    if not staff_user_ids:
        return []

    staff_users = User.query.filter(User.id.in_(staff_user_ids)).all()
    assignments = (
        StaffAssignment.query.filter(StaffAssignment.user_id.in_(staff_user_ids))
        .all()
    )

    location_names = {
        loc.id: loc.name
        for loc in CampusLocation.query.filter(CampusLocation.id.in_(location_ids)).all()
    }

    result = []
    for user in staff_users:
        user_assignments = [
            {
                "location_id": a.location_id,
                "location_name": location_names.get(a.location_id),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assignments
            if a.user_id == user.id
        ]
        result.append(
            {
                "user": serialize_user(user),
                "assignments": user_assignments,
            }
        )
    return result


def staff_activity(user, user_id):
    from app.custody.models import CustodyRecord

    location_ids = _scope_location_ids(user)
    if user.role == UserRole.SUPER_ADMIN:
        scoped = False
    elif user.role == UserRole.LOCATION_MANAGER:
        assigned = StaffAssignment.query.filter(
            StaffAssignment.user_id == user_id,
            StaffAssignment.location_id.in_(location_ids),
        ).first()
        if assigned is None:
            raise ApiError(
                "You do not have permission to view this staff member's activity",
                status=403,
            )
        scoped = True
    else:
        raise ApiError("You do not have permission to view staff activity", status=403)

    inspections = Inspection.query.filter_by(staff_id=user_id)
    found_reports = ItemReport.query.filter_by(
        reporter_id=user_id, report_type=ReportType.FOUND
    )
    custody_actions = CustodyRecord.query.filter(
        (CustodyRecord.authorized_by == user_id) | (CustodyRecord.staff_id == user_id)
    )
    if scoped:
        inspections = inspections.filter(Inspection.location_id.in_(location_ids))
        found_reports = found_reports.filter(ItemReport.location_id.in_(location_ids))
        custody_actions = custody_actions.filter(
            CustodyRecord.location_id.in_(location_ids)
        )

    return {
        "inspections": inspections.count(),
        "found_reports": found_reports.count(),
        "custody_actions": custody_actions.count(),
    }
