from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.feed import services as feed_services
from app.items.services import serialize_report_public
from app.utils import fail, ok

feed_bp = Blueprint("feed", __name__, url_prefix="/api/v1/feed")


def _parse_date_arg(value):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


@feed_bp.get("")
@jwt_required()
def get_feed():
    params = {
        "type": request.args.get("type"),
        "search": request.args.get("search"),
        "location_id": request.args.get("location_id", type=int),
        "category": request.args.get("category"),
        "sort": request.args.get("sort", "newest"),
        "page": request.args.get("page", 1, type=int),
        "per_page": min(request.args.get("per_page", 12, type=int), 50),
    }

    date_from_raw = request.args.get("date_from")
    date_to_raw = request.args.get("date_to")
    params["date_from"] = _parse_date_arg(date_from_raw) if date_from_raw else None
    params["date_to"] = _parse_date_arg(date_to_raw) if date_to_raw else None
    if date_from_raw and params["date_from"] is None:
        return fail("date_from must be a valid date (YYYY-MM-DD)", status=422)
    if date_to_raw and params["date_to"] is None:
        return fail("date_to must be a valid date (YYYY-MM-DD)", status=422)

    pagination = feed_services.query_feed(params)
    return ok(
        data={
            "items": [serialize_report_public(r) for r in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )
