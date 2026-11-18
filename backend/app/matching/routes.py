from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.items.models import ItemReport
from app.matching import services as matching_services
from app.utils import ok

matches_bp = Blueprint("matches", __name__, url_prefix="/api/v1/matches")


@matches_bp.get("")
@jwt_required()
def list_my_matches():
    user_id = int(get_jwt_identity())
    report_id = request.args.get("report_id", type=int)

    if report_id:
        report = ItemReport.query.filter_by(id=report_id, reporter_id=user_id).first()
        report_ids = [report_id] if report else []
    else:
        report_ids = [
            r.id
            for r in ItemReport.query.filter_by(reporter_id=user_id)
            .with_entities(ItemReport.id)
            .all()
        ]

    matches = matching_services.find_matches_for_report_ids(report_ids)
    return ok(data=[matching_services.serialize_match(m) for m in matches])
