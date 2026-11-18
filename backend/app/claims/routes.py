from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.claims import services as claim_services
from app.locations.services import user_has_location_access
from app.security.services import client_ip, enforce_rate_limit
from app.users.models import UserRole
from app.users.services import get_user_by_id
from app.utils import fail, ok

claims_bp = Blueprint("claims", __name__, url_prefix="/api/v1/claims")
handover_bp = Blueprint("handover", __name__, url_prefix="/api/v1/handover")


def _current_user():
    return get_user_by_id(int(get_jwt_identity()))


@claims_bp.post("")
@jwt_required()
def create_claim():
    enforce_rate_limit("claim_submit", client_ip(), 10, 3600)
    data = request.get_json(silent=True) or {}
    claimant = _current_user()
    claim = claim_services.submit_claim(
        claimant, data.get("report_id"), data.get("evidence")
    )
    return ok(
        data=claim_services.serialize_claim(claim, claimant),
        message="Claim submitted successfully",
        status=201,
    )


@claims_bp.get("/mine")
@jwt_required()
def my_claims():
    user = _current_user()
    claims = claim_services.list_my_claims(user)
    return ok(data=[claim_services.serialize_claim(c, user) for c in claims])


@claims_bp.post("/<int:claim_id>/resubmit")
@jwt_required()
def resubmit_claim(claim_id):
    claimant = _current_user()
    data = request.get_json(silent=True) or {}
    claim = claim_services.resubmit_claim(claimant, claim_id, data.get("evidence"))
    return ok(
        data=claim_services.serialize_claim(claim, claimant),
        message="Claim updated",
    )


@claims_bp.get("")
@jwt_required()
def list_claims():
    user = _current_user()
    if user.role not in (
        UserRole.LOCATION_MANAGER,
        UserRole.LOCATION_STAFF,
        UserRole.SUPER_ADMIN,
    ):
        return fail("You do not have permission to view claims", status=403)
    status = request.args.get("status")
    claims = claim_services.list_claims_for_location_access(user, status)
    return ok(data=[claim_services.serialize_claim(c, user) for c in claims])


@claims_bp.get("/<int:claim_id>")
@jwt_required()
def get_claim(claim_id):
    user = _current_user()
    claim = claim_services.get_claim(claim_id)
    authorized = (
        user.id == claim.claimant_id
        or claim_services.can_review_claim(user, claim)
        or user_has_location_access(user, claim.report.location_id)
    )
    if not authorized:
        return fail("You do not have permission to view this claim", status=403)
    return ok(data=claim_services.serialize_claim(claim, user))


@claims_bp.post("/<int:claim_id>/review")
@jwt_required()
def review_claim(claim_id):
    reviewer = _current_user()
    data = request.get_json(silent=True) or {}
    claim, code = claim_services.review_claim(
        reviewer, claim_id, data.get("decision"), data.get("note")
    )
    result = claim_services.serialize_claim(claim, reviewer)
    if code:
        result["collection_code"] = code
    return ok(data=result, message="Claim reviewed")


@handover_bp.post("/verify")
@jwt_required()
def verify_handover():
    enforce_rate_limit(
        "handover_verify",
        client_ip(),
        current_app.config["LOGIN_RATE_LIMIT"],
        current_app.config["LOGIN_RATE_WINDOW_SECONDS"],
    )
    verifier = _current_user()
    data = request.get_json(silent=True) or {}
    claim, report = claim_services.verify_handover_code(
        verifier, data.get("claim_id"), data.get("code")
    )
    return ok(
        data={
            "claim_id": claim.id,
            "report_id": report.id,
            "status": report.status,
        },
        message="Handover complete. Item marked as recovered.",
    )
