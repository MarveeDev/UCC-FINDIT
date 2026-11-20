from sqlalchemy import or_, update

from app.extensions import db
from app.items.models import ItemReport, ItemStatus, ReportType
from app.locations.models import CampusLocation, LocationManager, StaffAssignment
from app.users.models import User, UserRole
from app.users.services import serialize_user
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


def get_super_admin_overview():
    """Platform-wide aggregate statistics for the Super Admin dashboard."""
    from app.claims.models import ClaimStatus, OwnershipClaim

    return {
        "total_students": User.query.filter_by(role=UserRole.STUDENT).count(),
        "total_administrators": User.query.filter_by(role=UserRole.LOCATION_MANAGER).count(),
        "total_staff": User.query.filter_by(role=UserRole.LOCATION_STAFF).count(),
        "total_theatres": CampusLocation.query.count(),
        "total_lost": ItemReport.query.filter_by(report_type=ReportType.LOST).count(),
        "total_found": ItemReport.query.filter_by(report_type=ReportType.FOUND).count(),
        "pending_claims": OwnershipClaim.query.filter_by(
            status=ClaimStatus.PENDING
        ).count(),
        "recovered": ItemReport.query.filter_by(status=ItemStatus.RECOVERED).count(),
        "unassigned": ItemReport.query.filter(
            ItemReport.location_id.is_(None)
        ).count(),
    }


def list_administrators():
    """Return every administrator with their current theatre assignment."""
    admins = (
        User.query.filter_by(role=UserRole.LOCATION_MANAGER)
        .order_by(User.first_name, User.last_name)
        .all()
    )
    result = []
    for admin in admins:
        assignment = LocationManager.query.filter_by(user_id=admin.id).first()
        location = assignment.location if assignment else None
        result.append(
            {
                "user": serialize_user(admin),
                "location_id": location.id if location else None,
                "location_name": location.name if location else None,
            }
        )
    return result


def list_theatres():
    """Return every lecture theatre with assignment and report counts."""
    theatres = CampusLocation.query.order_by(CampusLocation.name).all()
    result = []
    for theatre in theatres:
        administrators = [
            serialize_user(m.user) for m in theatre.managers.all()
        ]
        result.append(
            {
                "id": theatre.id,
                "name": theatre.name,
                "description": theatre.description,
                "is_active": theatre.is_active,
                "administrator_count": len(administrators),
                "staff_count": theatre.staff_assignments.count(),
                "lost_count": ItemReport.query.filter_by(
                    location_id=theatre.id, report_type=ReportType.LOST
                ).count(),
                "found_count": ItemReport.query.filter_by(
                    location_id=theatre.id, report_type=ReportType.FOUND
                ).count(),
                "administrators": administrators,
            }
        )
    return result
