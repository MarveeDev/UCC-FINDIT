from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.items import services as item_services
from app.items import validators
from app.reporting.services import submit_report
from app.users.services import get_user_by_id
from app.utils import fail, ok

items_bp = Blueprint("items", __name__, url_prefix="/api/v1/reports")


@items_bp.post("")
@jwt_required()
def create_report():
    data = request.get_json(silent=True) or {}
    errors, cleaned = validators.validate_report(data)
    if errors:
        return fail("Validation failed", status=422, errors=errors)

    reporter = get_user_by_id(int(get_jwt_identity()))
    report = submit_report(reporter, cleaned)

    return ok(
        data=item_services.serialize_report_public(report),
        message="Report submitted successfully",
        status=201,
    )


@items_bp.get("/mine")
@jwt_required()
def my_reports():
    user = get_user_by_id(int(get_jwt_identity()))
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    pagination = item_services.list_my_reports(user, page, per_page)
    return ok(
        data={
            "items": [
                item_services.serialize_report_public(r) for r in pagination.items
            ],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@items_bp.get("/<int:report_id>")
@jwt_required()
def get_report(report_id):
    viewer = get_user_by_id(int(get_jwt_identity()))
    report = item_services.get_report(report_id)
    return ok(data=item_services.serialize_report_detail(report, viewer))
