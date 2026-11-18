import json
import re

from app.extensions import db
from app.items.models import ItemReport, ItemStatus, ReportType
from app.items.services import serialize_report_public
from app.matching.models import Match

# A potential match is recorded and notified when its score reaches this value.
MATCH_THRESHOLD = 50

# Statuses that are still eligible for matching. Recovered, closed and rejected
# reports are excluded so they never generate new matches.
_MATCHABLE_STATUSES = {
    ItemStatus.OPEN,
    ItemStatus.POSSIBLE_MATCH,
    ItemStatus.CLAIM_PENDING,
    ItemStatus.VERIFICATION_REQUIRED,
    ItemStatus.APPROVED_FOR_COLLECTION,
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "with", "for",
    "to", "is", "was", "it", "my", "its", "this", "that",
}


def _normalize(value):
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def _tokens(value):
    normalized = _normalize(value)
    return {t for t in normalized.split() if len(t) > 2 and t not in _STOPWORDS}


def _overlap(a_value, b_value):
    return len(_tokens(a_value) & _tokens(b_value))


def compute_match_score(lost, found):
    """Return a transparent (score, reasons) tuple for a lost/found pair.

    The score is a sum of explained rule contributions, capped at 100. Each
    non-zero contribution is paired with a human-readable reason.
    """
    reasons = []
    score = 0

    # Category: different categories are not a match unless one is "Other".
    if lost.category == found.category:
        score += 30
        reasons.append("Same category")
    elif lost.category == "Other" or found.category == "Other":
        reasons.append("Broad 'Other' category")
    else:
        return 0, ["Different categories"]

    # Item name.
    lost_name = _normalize(lost.item_name)
    found_name = _normalize(found.item_name)
    if lost_name and lost_name == found_name:
        score += 30
        reasons.append("Exact item name match")
    else:
        shared = _overlap(lost.item_name, found.item_name)
        if shared:
            score += min(15, shared * 5)
            reasons.append(f"Item name shares {shared} keyword(s)")

    # Brand.
    if lost.brand and found.brand and _normalize(lost.brand) == _normalize(found.brand):
        score += 15
        reasons.append("Matching brand")

    # Colour.
    if (
        lost.colour
        and found.colour
        and _normalize(lost.colour) == _normalize(found.colour)
    ):
        score += 10
        reasons.append("Matching colour")

    # Description keywords.
    shared_desc = _overlap(lost.description, found.description)
    if shared_desc:
        score += min(10, shared_desc * 2)
        reasons.append(f"{shared_desc} common description keyword(s)")

    # Location.
    if lost.location_id == found.location_id:
        score += 10
        reasons.append("Same location")

    # Date proximity.
    if lost.event_date and found.event_date:
        delta = abs((lost.event_date - found.event_date).days)
        if delta <= 3:
            score += 10
            reasons.append("Close dates")
        elif delta <= 7:
            score += 5
            reasons.append("Nearby dates")

    return min(score, 100), reasons


def evaluate_report(report):
    """Create match records between a report and opposite-type candidates.

    Idempotent: existing pairs are skipped (duplicate match records are
    prevented by both the unique constraint and the pre-check). Returns the
    list of newly created Match records.
    """
    other_type = (
        ReportType.FOUND if report.report_type == ReportType.LOST else ReportType.LOST
    )
    candidates = ItemReport.query.filter(
        ItemReport.report_type == other_type,
        ItemReport.status.in_(_MATCHABLE_STATUSES),
        ItemReport.id != report.id,
    ).all()

    created = []
    for candidate in candidates:
        lost = report if report.report_type == ReportType.LOST else candidate
        found = candidate if report.report_type == ReportType.LOST else report

        if Match.query.filter_by(
            lost_report_id=lost.id, found_report_id=found.id
        ).first():
            continue

        score, reasons = compute_match_score(lost, found)
        if score >= MATCH_THRESHOLD:
            match = Match(
                lost_report_id=lost.id,
                found_report_id=found.id,
                score=score,
                reasons=json.dumps(reasons),
            )
            db.session.add(match)
            created.append(match)

    if created:
        db.session.commit()
    return created


def find_matches_for_report_ids(report_ids):
    if not report_ids:
        return []
    return (
        Match.query.filter(
            Match.lost_report_id.in_(report_ids)
            | Match.found_report_id.in_(report_ids)
        )
        .order_by(Match.score.desc(), Match.created_at.desc())
        .all()
    )


def serialize_match(match):
    return {
        "id": match.id,
        "score": match.score,
        "reasons": json.loads(match.reasons) if match.reasons else [],
        "lost_report": serialize_report_public(match.lost_report),
        "found_report": serialize_report_public(match.found_report),
        "created_at": match.created_at.isoformat() if match.created_at else None,
    }
