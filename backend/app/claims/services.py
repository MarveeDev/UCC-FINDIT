import secrets
import string
from datetime import timedelta

from flask import current_app
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.claims.models import ClaimStatus, HandoverCode, OwnershipClaim
from app.extensions import db
from app.items.models import ItemReport, ItemStatus, ReportType
from app.items.services import serialize_report_public
from app.locations.models import LocationManager, StaffAssignment
from app.locations.services import user_has_location_access, user_manages_location
from app.notifications.models import NotificationType
from app.notifications.services import notify_claim_decision, notify_claim_submitted
from app.users.models import UserRole, utcnow
from app.utils import ApiError

# Unambiguous alphabet for human-typed collection codes.
_CODE_ALPHABET = "".join(
    c for c in string.ascii_uppercase + string.digits if c not in "O0I1"
)


def _display_name(user):
    if not user:
        return "Unknown"
    initial = f"{user.last_name[0]}." if user.last_name else ""
    return f"{user.first_name} {initial}".strip()


def can_review_claim(user, claim):
    """True for super admins and managers assigned to the report's location.

    Claimants can never review their own claim, even if they hold a manager
    role.
    """
    if user.id == claim.claimant_id:
        return False
    if user.role == UserRole.SUPER_ADMIN:
        return True
    if user.role == UserRole.LOCATION_MANAGER:
        return user_manages_location(user, claim.report.location_id)
    return False


def _can_view_evidence(claim, viewer):
    return viewer is not None and (
        viewer.id == claim.claimant_id or can_review_claim(viewer, claim)
    )


def serialize_claim(claim, viewer):
    data = {
        "id": claim.id,
        "report_id": claim.report_id,
        "status": claim.status,
        "claimant_name": _display_name(claim.claimant),
        "review_note": claim.review_note,
        "created_at": claim.created_at.isoformat() if claim.created_at else None,
        "reviewed_at": claim.reviewed_at.isoformat() if claim.reviewed_at else None,
        "report": serialize_report_public(claim.report),
    }
    if _can_view_evidence(claim, viewer):
        data["evidence"] = claim.evidence
    return data


def submit_claim(claimant, report_id, evidence):
    report = db.session.get(ItemReport, report_id)
    if report is None:
        raise ApiError("Report not found", status=404)
    if report.report_type != ReportType.FOUND:
        raise ApiError("You can only claim found items", status=400)
    if report.reporter_id == claimant.id:
        raise ApiError("You cannot claim an item you reported yourself", status=400)

    evidence = (evidence or "").strip()
    if not evidence:
        raise ApiError("Ownership evidence is required", status=422)
    if len(evidence) > 2000:
        raise ApiError("Ownership evidence is too long", status=422)

    existing = OwnershipClaim.query.filter_by(
        report_id=report_id, claimant_id=claimant.id
    ).first()
    if existing:
        raise ApiError("You have already submitted a claim for this item", status=409)

    claim = OwnershipClaim(
        report_id=report_id, claimant_id=claimant.id, evidence=evidence
    )
    report.status = ItemStatus.CLAIM_PENDING
    db.session.add(claim)
    db.session.commit()

    notify_claim_submitted(claim)
    return claim


def get_claim(claim_id):
    claim = db.session.get(OwnershipClaim, claim_id)
    if claim is None:
        raise ApiError("Claim not found", status=404)
    return claim


def list_my_claims(user):
    return (
        OwnershipClaim.query.filter_by(claimant_id=user.id)
        .order_by(OwnershipClaim.created_at.desc())
        .all()
    )


def resubmit_claim(claimant, claim_id, evidence):
    claim = get_claim(claim_id)
    if claim.claimant_id != claimant.id:
        raise ApiError("You do not have permission to update this claim", status=403)
    if claim.status != ClaimStatus.MORE_INFORMATION_REQUIRED:
        raise ApiError("This claim is not awaiting more information", status=400)

    evidence = (evidence or "").strip()
    if not evidence:
        raise ApiError("Ownership evidence is required", status=422)
    if len(evidence) > 2000:
        raise ApiError("Ownership evidence is too long", status=422)

    claim.evidence = evidence
    claim.status = ClaimStatus.PENDING
    claim.report.status = ItemStatus.CLAIM_PENDING
    db.session.commit()

    notify_claim_submitted(claim)
    return claim


def list_claims_for_location_access(user, status=None):
    """Claims visible to a manager/staff within their locations, or all for admin."""
    query = OwnershipClaim.query

    if user.role != UserRole.SUPER_ADMIN:
        if user.role == UserRole.LOCATION_MANAGER:
            location_ids = [
                m.location_id
                for m in LocationManager.query.filter_by(user_id=user.id).all()
            ]
        elif user.role == UserRole.LOCATION_STAFF:
            location_ids = [
                s.location_id
                for s in StaffAssignment.query.filter_by(user_id=user.id).all()
            ]
        else:
            return []
        if not location_ids:
            return []
        query = query.join(
            ItemReport, OwnershipClaim.report_id == ItemReport.id
        ).filter(ItemReport.location_id.in_(location_ids))

    if status:
        query = query.filter(OwnershipClaim.status == status)

    return query.order_by(OwnershipClaim.created_at.desc()).all()


def review_claim(reviewer, claim_id, decision, note):
    claim = get_claim(claim_id)
    if not can_review_claim(reviewer, claim):
        raise ApiError("You do not have permission to review this claim", status=403)
    if claim.status not in (ClaimStatus.PENDING, ClaimStatus.MORE_INFORMATION_REQUIRED):
        raise ApiError("This claim has already been decided", status=400)
    if decision not in ClaimStatus.ALL:
        raise ApiError("Invalid decision", status=422)

    if decision == ClaimStatus.APPROVED and _has_approved_claim(
        claim.report_id, exclude_claim_id=claim.id
    ):
        raise ApiError("Another claim has already been approved for this item", status=409)

    claim.status = decision
    claim.reviewer_id = reviewer.id
    claim.review_note = (note or "").strip() or None
    claim.reviewed_at = utcnow()

    if decision == ClaimStatus.APPROVED:
        claim.report.status = ItemStatus.APPROVED_FOR_COLLECTION
        _reject_other_claims(claim)
    elif decision == ClaimStatus.REJECTED:
        claim.report.status = ItemStatus.OPEN
    elif decision == ClaimStatus.MORE_INFORMATION_REQUIRED:
        claim.report.status = ItemStatus.VERIFICATION_REQUIRED

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("Another claim has already been approved for this item", status=409)

    code = None
    if decision == ClaimStatus.APPROVED:
        code = generate_handover_code(claim)

    _notify_decision(claim)
    return claim, code


def _has_approved_claim(report_id, exclude_claim_id=None):
    query = OwnershipClaim.query.filter(
        OwnershipClaim.report_id == report_id,
        OwnershipClaim.status == ClaimStatus.APPROVED,
    )
    if exclude_claim_id is not None:
        query = query.filter(OwnershipClaim.id != exclude_claim_id)
    return query.first() is not None


def _reject_other_claims(claim):
    """Reject any other undecided claims for the same item once one is approved."""
    OwnershipClaim.query.filter(
        OwnershipClaim.report_id == claim.report_id,
        OwnershipClaim.id != claim.id,
        OwnershipClaim.status.in_(
            [ClaimStatus.PENDING, ClaimStatus.MORE_INFORMATION_REQUIRED]
        ),
    ).update(
        {
            "status": ClaimStatus.REJECTED,
            "review_note": "Another claim was approved for this item",
            "reviewed_at": utcnow(),
        },
        synchronize_session=False,
    )


def _notify_decision(claim):
    mapping = {
        ClaimStatus.APPROVED: (NotificationType.CLAIM_APPROVED, "Claim approved"),
        ClaimStatus.REJECTED: (NotificationType.CLAIM_REJECTED, "Claim rejected"),
        ClaimStatus.MORE_INFORMATION_REQUIRED: (
            NotificationType.MORE_INFORMATION_REQUIRED,
            "More information required",
        ),
    }
    type_, title = mapping[claim.status]
    notify_claim_decision(claim, type_, title)


def generate_handover_code(claim):
    code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
    expires_at = utcnow() + timedelta(
        hours=current_app.config["HANDOVER_CODE_EXPIRY_HOURS"]
    )
    db.session.add(
        HandoverCode(
            claim_id=claim.id,
            code_hash=generate_password_hash(code),
            expires_at=expires_at,
        )
    )
    db.session.commit()
    # The plaintext is returned only here, at generation time.
    return code


def verify_handover_code(verifier, claim_id, code):
    claim = get_claim(claim_id)
    if claim.status != ClaimStatus.APPROVED:
        raise ApiError("This claim is not approved for collection", status=400)
    if not user_has_location_access(verifier, claim.report.location_id):
        raise ApiError("You do not have permission to complete this handover", status=403)

    record = claim.handover_codes.order_by(HandoverCode.created_at.desc()).first()
    if record is None or record.is_consumed:
        raise ApiError("No active collection code for this claim", status=400)
    if record.expires_at < utcnow():
        raise ApiError("This collection code has expired", status=400)
    if record.attempts >= current_app.config["HANDOVER_CODE_MAX_ATTEMPTS"]:
        raise ApiError("Too many attempts. This code is locked.", status=429)

    if not check_password_hash(record.code_hash, (code or "").strip()):
        record.attempts += 1
        db.session.commit()
        raise ApiError("Invalid collection code", status=400)

    # Atomically consume the code so concurrent verification requests cannot
    # both complete the same handover.
    result = db.session.execute(
        update(HandoverCode)
        .where(HandoverCode.id == record.id, HandoverCode.is_consumed.is_(False))
        .values(
            is_consumed=True,
            consumed_at=utcnow(),
            verified_by=verifier.id,
        )
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise ApiError("This collection code has already been used", status=400)

    claim.report.status = ItemStatus.RECOVERED
    db.session.commit()
    return claim, claim.report
