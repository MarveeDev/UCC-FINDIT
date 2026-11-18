from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.items import validators as item_validators
from app.items.services import serialize_report_public
from app.notifications.services import notify_qr_item_found
from app.qr import services as qr_services
from app.reporting.services import submit_report
from app.security.services import client_ip, enforce_rate_limit
from app.users.services import get_user_by_id
from app.utils import fail, ok

qr_bp = Blueprint("qr", __name__, url_prefix="/api/v1/qr")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


@qr_bp.post("")
@jwt_required()
def register_qr():
    user = _current_user()
    data = request.get_json(silent=True) or {}
    qr = qr_services.register_qr(user, data.get("item_name"), data.get("description"))
    return ok(
        data=qr_services.serialize_qr(qr, include_token=True),
        message="Item registered with QR code",
        status=201,
    )


@qr_bp.get("/mine")
@jwt_required()
def my_qr():
    user = _current_user()
    qrs = qr_services.list_my_qr(user)
    return ok(data=[qr_services.serialize_qr(q, include_token=True) for q in qrs])


@qr_bp.post("/<int:qr_id>/deactivate")
@jwt_required()
def deactivate_qr(qr_id):
    user = _current_user()
    qr = qr_services.deactivate_qr(user, qr_id)
    return ok(
        data=qr_services.serialize_qr(qr, include_token=True),
        message="QR code deactivated",
    )


@qr_bp.get("/<token>")
@jwt_required()
def lookup_qr(token):
    qr = qr_services.get_by_token(token)
    if qr is None or not qr.is_active:
        return fail("QR code not found", status=404)
    # No owner identity or contact information is returned.
    return ok(data=qr_services.serialize_qr(qr, include_token=False))


@qr_bp.post("/<token>/report-found")
@jwt_required()
def report_found(token):
    enforce_rate_limit(
        "qr_report_found",
        client_ip(),
        current_app.config["VERIFY_RATE_LIMIT"],
        current_app.config["VERIFY_RATE_WINDOW_SECONDS"],
    )
    finder = _current_user()
    qr = qr_services.get_by_token(token)
    if qr is None or not qr.is_active:
        return fail("QR code not found", status=404)

    data = request.get_json(silent=True) or {}
    data["report_type"] = "FOUND"
    if not data.get("item_name"):
        data["item_name"] = qr.item_name

    errors, cleaned = item_validators.validate_report(data)
    if errors:
        return fail("Validation failed", status=422, errors=errors)

    report = submit_report(finder, cleaned)
    notify_qr_item_found(qr, report)

    return ok(
        data=serialize_report_public(report),
        message="Report submitted successfully",
        status=201,
    )
