from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.audit.models import AuditLog
from app.audit.services import serialize_audit_log
from app.locations.models import LocationManager
from app.users.models import UserRole
from app.users.services import get_user_by_id
from app.utils import fail, ok

audit_bp = Blueprint("audit", __name__, url_prefix="/api/v1/audit-logs")


@audit_bp.get("")
@jwt_required()
def list_audit_logs():
    user = get_user_by_id(int(get_jwt_identity()))

    if user.role not in (UserRole.SUPER_ADMIN, UserRole.LOCATION_MANAGER):
        return fail("You do not have permission to view audit logs", status=403)

    query = AuditLog.query
    if user.role != UserRole.SUPER_ADMIN:
        location_ids = [
            m.location_id
            for m in LocationManager.query.filter_by(user_id=user.id).all()
        ]
        query = query.filter(
            (AuditLog.location_id.in_(location_ids))
            | ((AuditLog.location_id.is_(None)) & (AuditLog.actor_id == user.id))
        )

    location_id = request.args.get("location_id", type=int)
    if location_id:
        query = query.filter(AuditLog.location_id == location_id)

    action = request.args.get("action")
    if action:
        query = query.filter(AuditLog.action == action)

    entity_type = request.args.get("entity_type")
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 50, type=int), 100)
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return ok(
        data={
            "items": [serialize_audit_log(log) for log in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )
