from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.audit.services import INSPECTION_CONVERTED, INSPECTION_CREATED, record_audit
from app.inspections import services as inspection_services
from app.items import validators as item_validators
from app.items.services import serialize_report_public
from app.locations.services import user_has_location_access
from app.users.services import get_user_by_id
from app.utils import fail, ok

inspections_bp = Blueprint("inspections", __name__, url_prefix="/api/v1/inspections")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


@inspections_bp.post("")
@jwt_required()
def create_inspection():
    user = _current_user()
    data = request.get_json(silent=True) or {}
    if not (data.get("item_description") or "").strip():
        return fail("Item description is required", status=422)
    if not (data.get("category") or "").strip():
        return fail("Category is required", status=422)

    inspection = inspection_services.create_inspection(user, data)
    record_audit(
        user.id,
        INSPECTION_CREATED,
        "inspection",
        inspection.id,
        inspection.location_id,
    )
    return ok(
        data=inspection_services.serialize_inspection(inspection),
        message="Inspection recorded",
        status=201,
    )


@inspections_bp.get("")
@jwt_required()
def list_inspections():
    user = _current_user()
    location_id = request.args.get("location_id", type=int)
    status = request.args.get("status")
    inspections = inspection_services.list_inspections(user, location_id, status)
    return ok(data=[inspection_services.serialize_inspection(i) for i in inspections])


@inspections_bp.get("/<int:inspection_id>")
@jwt_required()
def get_inspection(inspection_id):
    user = _current_user()
    inspection = inspection_services.get_inspection(inspection_id)
    if user.id != inspection.staff_id and not user_has_location_access(
        user, inspection.location_id
    ):
        return fail("You do not have permission to view this inspection", status=403)
    return ok(data=inspection_services.serialize_inspection(inspection))


@inspections_bp.post("/<int:inspection_id>/convert")
@jwt_required()
def convert_inspection(inspection_id):
    user = _current_user()
    inspection = inspection_services.get_inspection(inspection_id)
    if not user_has_location_access(user, inspection.location_id):
        return fail("You do not have permission to convert this inspection", status=403)

    data = request.get_json(silent=True) or {}
    payload = {
        "report_type": "FOUND",
        "item_name": (data.get("item_name") or "").strip()
        or (inspection.item_description or "")[:120],
        "category": (data.get("category") or "").strip() or inspection.category,
        "description": (data.get("description") or "").strip() or inspection.item_description,
        "brand": (data.get("brand") or "").strip() or inspection.brand,
        "colour": (data.get("colour") or "").strip() or inspection.colour,
        "location_id": data.get("location_id") or inspection.location_id,
        "event_date": (data.get("event_date") or "").strip() or date.today().isoformat(),
        "custody_info": inspection.notes,
    }
    errors, cleaned = item_validators.validate_report(payload)
    if errors:
        return fail("Validation failed", status=422, errors=errors)

    inspection, report = inspection_services.convert_to_found_report(
        inspection, user, cleaned
    )
    record_audit(
        user.id,
        INSPECTION_CONVERTED,
        "inspection",
        inspection.id,
        inspection.location_id,
        metadata={"found_report_id": report.id},
    )
    return ok(
        data={
            "inspection": inspection_services.serialize_inspection(inspection),
            "report": serialize_report_public(report),
        },
        message="Inspection converted to found report",
    )
