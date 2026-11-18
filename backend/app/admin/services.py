from sqlalchemy import or_, update

from app.extensions import db
from app.items.models import ItemReport
from app.locations.models import CampusLocation
from app.utils import ApiError


def list_unassigned_reports(page, per_page, search=None, report_type=None, status=None, sort="newest"):
    """Paginated list of reports with no registered campus location."""
    query = ItemReport.query.filter(ItemReport.location_id.is_(None))

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                ItemReport.item_name.ilike(like),
                ItemReport.location_description.ilike(like),
            )
        )

    if report_type:
        query = query.filter(ItemReport.report_type == report_type.upper())

    if status:
        query = query.filter(ItemReport.status == status.upper())

    if sort == "oldest":
        query = query.order_by(ItemReport.created_at.asc())
    else:
        query = query.order_by(ItemReport.created_at.desc())

    return query.paginate(page=page, per_page=per_page, error_out=False)


def assign_report(report_id, location_id):
    """Atomically assign an unassigned report to a registered location.

    Returns the updated report. The original location_description and
    latitude/longitude are preserved (only location_id changes).
    """
    report = db.session.get(ItemReport, report_id)
    if report is None:
        raise ApiError("Report not found", status=404)
    if report.location_id is not None:
        raise ApiError("This report is already assigned to a location", status=409)

    location = db.session.get(CampusLocation, location_id)
    if location is None or not location.is_active:
        raise ApiError("Selected location is not valid", status=400)

    # Conditional update guards against concurrent double-assignment.
    result = db.session.execute(
        update(ItemReport)
        .where(ItemReport.id == report.id, ItemReport.location_id.is_(None))
        .values(location_id=location_id)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise ApiError("This report has already been assigned", status=409)

    db.session.commit()
    db.session.refresh(report)
    return report
