from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.items.models import ItemReport, ItemStatus, ReportType


def query_feed(params):
    query = ItemReport.query.options(
        joinedload(ItemReport.location), joinedload(ItemReport.reporter)
    )

    report_type = params.get("type")
    if report_type == "lost":
        query = query.filter(ItemReport.report_type == ReportType.LOST)
    elif report_type == "found":
        query = query.filter(ItemReport.report_type == ReportType.FOUND)
    elif report_type == "recovered":
        query = query.filter(ItemReport.status == ItemStatus.RECOVERED)

    search = (params.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                ItemReport.item_name.ilike(like),
                ItemReport.description.ilike(like),
                ItemReport.brand.ilike(like),
            )
        )

    if params.get("location_id"):
        query = query.filter(ItemReport.location_id == params["location_id"])

    if params.get("category"):
        query = query.filter(ItemReport.category == params["category"])

    if params.get("date_from"):
        query = query.filter(ItemReport.event_date >= params["date_from"])
    if params.get("date_to"):
        query = query.filter(ItemReport.event_date <= params["date_to"])

    sort = params.get("sort", "newest")
    if sort == "oldest":
        query = query.order_by(ItemReport.created_at.asc())
    else:
        query = query.order_by(ItemReport.created_at.desc())

    return query.paginate(
        page=params["page"], per_page=params["per_page"], error_out=False
    )
