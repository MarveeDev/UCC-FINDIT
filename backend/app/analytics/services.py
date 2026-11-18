from datetime import date

from sqlalchemy import func

from app.claims.models import ClaimStatus, HandoverCode, OwnershipClaim
from app.custody.models import CustodyRecord
from app.extensions import db
from app.inspections.models import Inspection
from app.items.models import ItemReport, ItemStatus, ReportType
from app.items.services import serialize_report_public
from app.locations.models import CampusLocation, LocationManager, StaffAssignment
from app.users.models import User, UserRole


def _scope_location_ids(user):
    if user.role == UserRole.SUPER_ADMIN:
        return [
            loc.id for loc in CampusLocation.query.with_entities(CampusLocation.id).all()
        ]
    if user.role == UserRole.LOCATION_MANAGER:
        return [m.location_id for m in LocationManager.query.filter_by(user_id=user.id).all()]
    return []


def _apply_report_filters(query, location_ids, date_from, date_to, category=None, status=None):
    query = query.filter(ItemReport.location_id.in_(location_ids))
    if date_from:
        query = query.filter(ItemReport.event_date >= date_from)
    if date_to:
        query = query.filter(ItemReport.event_date <= date_to)
    if category:
        query = query.filter(ItemReport.category == category)
    if status:
        query = query.filter(ItemReport.status == status)
    return query


def get_dashboard(user, location_id=None, date_from=None, date_to=None):
    location_ids = _scope_location_ids(user)
    if not location_ids:
        return empty_dashboard()

    if location_id is not None and location_id in location_ids:
        location_ids = [location_id]

    lost = _apply_report_filters(ItemReport.query, location_ids, date_from, date_to).filter(
        ItemReport.report_type == ReportType.LOST
    ).count()
    found = _apply_report_filters(ItemReport.query, location_ids, date_from, date_to).filter(
        ItemReport.report_type == ReportType.FOUND
    ).count()
    recovered = _apply_report_filters(ItemReport.query, location_ids, date_from, date_to).filter(
        ItemReport.status == ItemStatus.RECOVERED
    ).count()
    awaiting = _apply_report_filters(ItemReport.query, location_ids, date_from, date_to).filter(
        ItemReport.status == ItemStatus.APPROVED_FOR_COLLECTION
    ).count()
    pending_claims = (
        OwnershipClaim.query.join(ItemReport, OwnershipClaim.report_id == ItemReport.id)
        .filter(ItemReport.location_id.in_(location_ids), OwnershipClaim.status == ClaimStatus.PENDING)
        .count()
    )
    active_staff = (
        db.session.query(func.count(func.distinct(StaffAssignment.user_id)))
        .filter(StaffAssignment.location_id.in_(location_ids))
        .scalar()
        or 0
    )

    recent_reports = (
        ItemReport.query.filter(ItemReport.location_id.in_(location_ids))
        .order_by(ItemReport.created_at.desc())
        .limit(5)
        .all()
    )
    pending_claim_rows = (
        OwnershipClaim.query.join(ItemReport, OwnershipClaim.report_id == ItemReport.id)
        .filter(ItemReport.location_id.in_(location_ids), OwnershipClaim.status == ClaimStatus.PENDING)
        .order_by(OwnershipClaim.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "metrics": {
            "lost": lost,
            "found": found,
            "recovered": recovered,
            "awaiting_collection": awaiting,
            "pending_claims": pending_claims,
            "active_staff": active_staff,
        },
        "recent_reports": [serialize_report_public(r) for r in recent_reports],
        "pending_claim_summaries": [
            {
                "id": c.id,
                "report_id": c.report_id,
                "item_name": c.report.item_name,
                "claimant_name": _display_name(c.claimant),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in pending_claim_rows
        ],
    }


def empty_dashboard():
    return {
        "metrics": {
            "lost": 0, "found": 0, "recovered": 0,
            "awaiting_collection": 0, "pending_claims": 0, "active_staff": 0,
        },
        "recent_reports": [],
        "pending_claim_summaries": [],
    }


def _display_name(user):
    if not user:
        return "Unknown"
    initial = f"{user.last_name[0]}." if user.last_name else ""
    return f"{user.first_name} {initial}".strip()


def get_analytics(user, date_from=None, date_to=None, location_id=None, category=None):
    location_ids = _scope_location_ids(user)
    if not location_ids:
        return empty_analytics()
    if location_id is not None and location_id in location_ids:
        location_ids = [location_id]

    base = ItemReport.query.filter(ItemReport.location_id.in_(location_ids))
    if date_from:
        base = base.filter(ItemReport.event_date >= date_from)
    if date_to:
        base = base.filter(ItemReport.event_date <= date_to)
    if category:
        base = base.filter(ItemReport.category == category)

    lost = base.filter(ItemReport.report_type == ReportType.LOST).count()
    found = base.filter(ItemReport.report_type == ReportType.FOUND).count()
    recovered = base.filter(ItemReport.status == ItemStatus.RECOVERED).count()
    recovery_rate = round((recovered / found) * 100, 1) if found else 0.0
    pending_claims = (
        OwnershipClaim.query.join(ItemReport, OwnershipClaim.report_id == ItemReport.id)
        .filter(ItemReport.location_id.in_(location_ids), OwnershipClaim.status == ClaimStatus.PENDING)
        .count()
    )

    return {
        "lost": lost,
        "found": found,
        "recovered": recovered,
        "recovery_rate": recovery_rate,
        "pending_claims": pending_claims,
        "avg_recovery_days": _avg_recovery_days(location_ids),
        "by_location": _by_location(location_ids, date_from, date_to),
        "by_category": _by_category(location_ids, date_from, date_to),
        "staff_activity": _staff_activity(location_ids),
    }


def empty_analytics():
    return {
        "lost": 0, "found": 0, "recovered": 0, "recovery_rate": 0.0,
        "pending_claims": 0, "avg_recovery_days": None,
        "by_location": [], "by_category": [], "staff_activity": [],
    }


def _avg_recovery_days(location_ids):
    rows = (
        db.session.query(ItemReport.created_at, HandoverCode.consumed_at)
        .join(OwnershipClaim, OwnershipClaim.report_id == ItemReport.id)
        .join(HandoverCode, HandoverCode.claim_id == OwnershipClaim.id)
        .filter(
            ItemReport.status == ItemStatus.RECOVERED,
            HandoverCode.is_consumed.is_(True),
            ItemReport.location_id.in_(location_ids),
        )
        .all()
    )
    if not rows:
        return None
    total_seconds = sum(
        (consumed - created).total_seconds()
        for created, consumed in rows
        if consumed and created
    )
    return round(total_seconds / (len(rows) * 86400), 1)


def _by_location(location_ids, date_from, date_to):
    query = (
        db.session.query(
            CampusLocation.name,
            func.count(ItemReport.id),
            ItemReport.report_type,
        )
        .join(ItemReport, ItemReport.location_id == CampusLocation.id)
        .filter(ItemReport.location_id.in_(location_ids))
    )
    if date_from:
        query = query.filter(ItemReport.event_date >= date_from)
    if date_to:
        query = query.filter(ItemReport.event_date <= date_to)
    rows = query.group_by(CampusLocation.name, ItemReport.report_type).all()

    result = {}
    for name, count, rtype in rows:
        bucket = result.setdefault(name, {"location": name, "lost": 0, "found": 0})
        if rtype == ReportType.LOST:
            bucket["lost"] = count
        else:
            bucket["found"] = count
    return list(result.values())


def _by_category(location_ids, date_from, date_to):
    query = (
        db.session.query(ItemReport.category, func.count(ItemReport.id))
        .filter(ItemReport.location_id.in_(location_ids))
    )
    if date_from:
        query = query.filter(ItemReport.event_date >= date_from)
    if date_to:
        query = query.filter(ItemReport.event_date <= date_to)
    return [
        {"category": cat, "count": count}
        for cat, count in query.group_by(ItemReport.category).order_by(
            func.count(ItemReport.id).desc()
        ).all()
    ]


def _staff_activity(location_ids):
    inspection_rows = (
        db.session.query(Inspection.staff_id, func.count(Inspection.id))
        .filter(Inspection.location_id.in_(location_ids))
        .group_by(Inspection.staff_id)
        .all()
    )
    custody_rows = (
        db.session.query(CustodyRecord.authorized_by, func.count(CustodyRecord.id))
        .filter(CustodyRecord.location_id.in_(location_ids))
        .group_by(CustodyRecord.authorized_by)
        .all()
    )

    activity = {}
    for staff_id, count in inspection_rows:
        activity.setdefault(staff_id, {"inspections": 0, "custody_actions": 0})[
            "inspections"
        ] = count
    for staff_id, count in custody_rows:
        activity.setdefault(staff_id, {"inspections": 0, "custody_actions": 0})[
            "custody_actions"
        ] = count

    users = {u.id: u for u in User.query.filter(User.id.in_(activity.keys())).all()}
    return [
        {
            "staff_id": staff_id,
            "staff_name": _display_name(users.get(staff_id)),
            "inspections": counts["inspections"],
            "custody_actions": counts["custody_actions"],
        }
        for staff_id, counts in activity.items()
    ]
