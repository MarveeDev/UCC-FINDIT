from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity

from app.admin import services as admin_services
from app.audit.services import REPORT_ASSIGNED, record_audit
from app.items.services import serialize_report_public
from app.notifications.services import notify_report_assignment
from app.users.models import UserRole
from app.users.services import get_user_by_id
from app.utils import fail, ok
from app.utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/v1/admin")


@admin_bp.get("/overview")
@role_required(UserRole.SUPER_ADMIN)
def super_admin_overview():
    return ok(data=admin_services.get_super_admin_overview())


@admin_bp.get("/administrators")
@role_required(UserRole.SUPER_ADMIN)
def list_administrators():
    return ok(data=admin_services.list_administrators())


@admin_bp.get("/theatres")
@role_required(UserRole.SUPER_ADMIN)
def list_theatres():
    return ok(data=admin_services.list_theatres())


@admin_bp.get("/unassigned-reports")
@role_required(UserRole.SUPER_ADMIN)
def list_unassigned_reports():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 50)
    search = request.args.get("search")
    report_type = request.args.get("report_type")
    status = request.args.get("status")
    sort = request.args.get("sort", "newest")

    pagination = admin_services.list_unassigned_reports(
        page, per_page, search, report_type, status, sort
    )
    return ok(
        data={
            "items": [serialize_report_public(r) for r in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@admin_bp.post("/reports/<int:report_id>/assign")
@role_required(UserRole.SUPER_ADMIN)
def assign_report(report_id):
    data = request.get_json(silent=True) or {}
    location_id = data.get("location_id")
    if location_id is None:
        return fail("location_id is required", status=422)

    report = admin_services.assign_report(report_id, int(location_id))
    notify_report_assignment(report)

    actor = get_user_by_id(int(get_jwt_identity()))
    record_audit(
        actor.id,
        REPORT_ASSIGNED,
        "report",
        report.id,
        report.location_id,
        metadata={
            "previous_location_id": None,
            "new_location_id": report.location_id,
        },
    )
    return ok(data=serialize_report_public(report), message="Report assigned to location")
