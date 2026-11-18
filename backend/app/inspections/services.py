import secrets
from datetime import datetime

from app.extensions import db
from app.inspections.models import Inspection, InspectionStatus
from app.items.models import ItemStatus
from app.locations.models import CampusLocation, LocationManager, StaffAssignment
from app.locations.services import user_has_location_access
from app.users.models import UserRole, utcnow
from app.utils import ApiError


def _new_reference():
    return "INS-" + secrets.token_hex(4).upper()


def _display_name(user):
    if not user:
        return "Unknown"
    initial = f"{user.last_name[0]}." if user.last_name else ""
    return f"{user.first_name} {initial}".strip()


def serialize_inspection(inspection):
    return {
        "id": inspection.id,
        "reference": inspection.reference,
        "location_id": inspection.location_id,
        "location_name": inspection.location.name if inspection.location else None,
        "staff_id": inspection.staff_id,
        "staff_name": _display_name(inspection.staff),
        "inspected_at": inspection.inspected_at.isoformat() if inspection.inspected_at else None,
        "item_description": inspection.item_description,
        "category": inspection.category,
        "colour": inspection.colour,
        "brand": inspection.brand,
        "image_url": f"/api/v1/uploads/{inspection.image_path}" if inspection.image_path else None,
        "notes": inspection.notes,
        "found_report_id": inspection.found_report_id,
        "status": inspection.status,
        "created_at": inspection.created_at.isoformat() if inspection.created_at else None,
    }


def create_inspection(staff, data):
    location_id = data.get("location_id")
    if not user_has_location_access(staff, location_id):
        raise ApiError("You do not have permission to inspect this location", status=403)

    location = db.session.get(CampusLocation, location_id)
    if location is None or not location.is_active:
        raise ApiError("Selected location is not valid", status=400)

    inspected_at = data.get("inspected_at") or utcnow()
    if isinstance(inspected_at, str):
        try:
            inspected_at = datetime.fromisoformat(inspected_at)
        except ValueError:
            raise ApiError("inspected_at must be a valid ISO datetime", status=422)

    inspection = Inspection(
        reference=_new_reference(),
        location_id=location_id,
        staff_id=staff.id,
        inspected_at=inspected_at,
        item_description=(data.get("item_description") or "").strip(),
        category=(data.get("category") or "").strip(),
        colour=(data.get("colour") or "").strip() or None,
        brand=(data.get("brand") or "").strip() or None,
        image_path=(data.get("image_path") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(inspection)
    db.session.commit()
    return inspection


def get_inspection(inspection_id):
    inspection = db.session.get(Inspection, inspection_id)
    if inspection is None:
        raise ApiError("Inspection not found", status=404)
    return inspection


def _visible_location_ids(user):
    if user.role == UserRole.SUPER_ADMIN:
        return [loc.id for loc in CampusLocation.query.with_entities(CampusLocation.id).all()]
    if user.role == UserRole.LOCATION_MANAGER:
        return [m.location_id for m in LocationManager.query.filter_by(user_id=user.id).all()]
    if user.role == UserRole.LOCATION_STAFF:
        return [s.location_id for s in StaffAssignment.query.filter_by(user_id=user.id).all()]
    return []


def list_inspections(user, location_id=None, status=None):
    query = Inspection.query

    if user.role == UserRole.SUPER_ADMIN:
        pass
    elif user.role in (UserRole.LOCATION_MANAGER, UserRole.LOCATION_STAFF):
        location_ids = _visible_location_ids(user)
        if not location_ids:
            return []
        query = query.filter(Inspection.location_id.in_(location_ids))
    else:
        return []

    if location_id:
        query = query.filter(Inspection.location_id == location_id)
    if status:
        query = query.filter(Inspection.status == status)

    return query.order_by(Inspection.inspected_at.desc()).all()


def convert_to_found_report(inspection, reporter, cleaned):
    from sqlalchemy import update

    from app.items.services import build_report
    from app.reporting.services import run_side_effects

    # Stage the found report, then atomically claim the conversion with a
    # conditional update so concurrent requests cannot create duplicate reports.
    report = build_report(reporter, cleaned)
    db.session.flush()

    result = db.session.execute(
        update(Inspection)
        .where(
            Inspection.id == inspection.id,
            Inspection.status == InspectionStatus.OPEN,
        )
        .values(
            status=InspectionStatus.CONVERTED,
            found_report_id=report.id,
        )
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise ApiError("This inspection has already been converted", status=409)

    db.session.commit()
    db.session.refresh(inspection)
    run_side_effects(report)
    return inspection, report
