from app.extensions import db
from app.items.models import ItemReport, ItemStatus
from app.locations.models import CampusLocation
from app.locations.services import user_manages_location
from app.utils import ApiError


def _display_name(user):
    if not user:
        return "Unknown"
    initial = f"{user.last_name[0]}." if user.last_name else ""
    return f"{user.first_name} {initial}".strip()


def serialize_report_public(report):
    """Privacy-safe representation used by the community feed and item detail.

    Deliberately excludes identifying characteristics, custody notes, and any
    reporter contact information (email, phone).
    """
    return {
        "id": report.id,
        "report_type": report.report_type,
        "item_name": report.item_name,
        "category": report.category,
        "description": report.description,
        "brand": report.brand,
        "colour": report.colour,
        "location_id": report.location_id,
        "location_name": report.location.name if report.location else None,
        "event_date": report.event_date.isoformat() if report.event_date else None,
        "event_time": report.event_time.isoformat() if report.event_time else None,
        "status": report.status,
        "image_url": f"/api/v1/uploads/{report.image_path}" if report.image_path else None,
        "reporter_name": _display_name(report.reporter),
        "created_at": report.created_at.isoformat() if report.created_at else None,
    }


def serialize_report_detail(report, viewer):
    """Detail view: adds confidential fields only for the reporter or a manager
    of the report's location."""
    data = serialize_report_public(report)
    can_view_private = viewer is not None and (
        viewer.id == report.reporter_id
        or user_manages_location(viewer, report.location_id)
    )
    if can_view_private:
        data["identifying_characteristics"] = report.identifying_characteristics
        data["custody_info"] = report.custody_info
    return data


def create_report(reporter, data):
    location = db.session.get(CampusLocation, data["location_id"])
    if location is None or not location.is_active:
        raise ApiError("Selected location is not valid", status=400)

    report = ItemReport(
        reporter_id=reporter.id,
        report_type=data["report_type"],
        item_name=data["item_name"],
        category=data["category"],
        description=data["description"],
        brand=data.get("brand"),
        colour=data.get("colour"),
        identifying_characteristics=data.get("identifying_characteristics"),
        location_id=data["location_id"],
        event_date=data["event_date"],
        event_time=data.get("event_time"),
        image_path=data.get("image_path"),
        custody_info=data.get("custody_info"),
        status=ItemStatus.OPEN,
    )
    db.session.add(report)
    db.session.commit()
    return report


def get_report(report_id):
    report = db.session.get(ItemReport, report_id)
    if report is None:
        raise ApiError("Report not found", status=404)
    return report


def list_my_reports(user, page, per_page):
    query = (
        ItemReport.query.filter_by(reporter_id=user.id)
        .order_by(ItemReport.created_at.desc())
    )
    return query.paginate(page=page, per_page=per_page, error_out=False)
