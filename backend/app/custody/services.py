from app.custody.models import CustodyEventType, CustodyRecord
from app.extensions import db
from app.items.models import ItemReport, ItemStatus, ReportType
from app.locations.models import CampusLocation
from app.locations.services import user_has_location_access
from app.users.models import User, UserRole
from app.utils import ApiError


def _display_name(user):
    if not user:
        return None
    initial = f"{user.last_name[0]}." if user.last_name else ""
    return f"{user.first_name} {initial}".strip()


def serialize_custody(record):
    return {
        "id": record.id,
        "found_report_id": record.found_report_id,
        "event_type": record.event_type,
        "staff_id": record.staff_id,
        "staff_name": _display_name(record.staff),
        "location_id": record.location_id,
        "location_name": record.location.name if record.location else None,
        "authorized_by": record.authorized_by,
        "authorizer_name": _display_name(record.authorizer),
        "note": record.note,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def record_custody(authorizer, found_report_id, event_type, staff_id, location_id, note=None):
    report = db.session.get(ItemReport, found_report_id)
    if report is None or report.report_type != ReportType.FOUND:
        raise ApiError("Custody applies to found items only", status=400)

    if event_type not in (
        CustodyEventType.RECEIVED,
        CustodyEventType.TRANSFERRED,
        CustodyEventType.RELEASED,
    ):
        raise ApiError("Invalid custody event type", status=422)

    if report.status == ItemStatus.RECOVERED and event_type != CustodyEventType.RELEASED:
        raise ApiError("Cannot record custody for a recovered item", status=400)

    if not user_has_location_access(authorizer, report.location_id):
        raise ApiError("You do not have permission to manage custody for this item", status=403)

    holder = db.session.get(User, staff_id) if staff_id else None
    if holder is None or holder.role not in (
        UserRole.LOCATION_STAFF,
        UserRole.LOCATION_MANAGER,
        UserRole.SUPER_ADMIN,
    ):
        raise ApiError("Invalid staff member", status=422)

    location = db.session.get(CampusLocation, location_id) if location_id else None
    if location is None or not location.is_active:
        raise ApiError("Invalid storage location", status=422)

    if not user_has_location_access(holder, location_id):
        raise ApiError(
            "The receiving staff member is not authorized for this location", status=422
        )

    record = CustodyRecord(
        found_report_id=found_report_id,
        event_type=event_type,
        staff_id=staff_id,
        location_id=location_id,
        authorized_by=authorizer.id,
        note=(note or "").strip() or None,
    )
    db.session.add(record)
    db.session.commit()
    return record


def list_custody(found_report_id):
    return (
        CustodyRecord.query.filter_by(found_report_id=found_report_id)
        .order_by(CustodyRecord.created_at.asc())
        .all()
    )


def current_custody(found_report_id):
    return (
        CustodyRecord.query.filter_by(found_report_id=found_report_id)
        .order_by(CustodyRecord.created_at.desc())
        .first()
    )
