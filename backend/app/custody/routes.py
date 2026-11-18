from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.audit.services import CUSTODY_RECEIVED, CUSTODY_TRANSFERRED, record_audit
from app.custody import services as custody_services
from app.custody.models import CustodyEventType
from app.users.services import get_user_by_id
from app.utils import fail, ok

custody_bp = Blueprint("custody", __name__, url_prefix="/api/v1/custody")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


@custody_bp.post("")
@jwt_required()
def create_custody():
    user = _current_user()
    data = request.get_json(silent=True) or {}
    event_type = (data.get("event_type") or "").strip().upper()
    if event_type not in (CustodyEventType.RECEIVED, CustodyEventType.TRANSFERRED):
        return fail("event_type must be RECEIVED or TRANSFERRED", status=422)

    found_report_id = data.get("found_report_id")
    if found_report_id is None:
        return fail("found_report_id is required", status=422)

    record = custody_services.record_custody(
        user,
        found_report_id,
        event_type,
        data.get("staff_id"),
        data.get("location_id"),
        data.get("note"),
    )
    action = CUSTODY_RECEIVED if event_type == CustodyEventType.RECEIVED else CUSTODY_TRANSFERRED
    record_audit(
        user.id,
        action,
        "custody",
        record.id,
        record.location_id,
        metadata={"found_report_id": found_report_id},
    )
    return ok(data=custody_services.serialize_custody(record), status=201)


@custody_bp.get("/<int:found_report_id>")
@jwt_required()
def get_custody_history(found_report_id):
    records = custody_services.list_custody(found_report_id)
    return ok(data=[custody_services.serialize_custody(r) for r in records])
