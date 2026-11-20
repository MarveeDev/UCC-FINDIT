import json

from app.audit.models import AuditLog
from app.extensions import db
from app.users.services import serialize_user

# Audit action constants.
STAFF_ASSIGNED = "STAFF_ASSIGNED"
STAFF_REMOVED = "STAFF_REMOVED"
REPORT_ASSIGNED = "REPORT_ASSIGNED"
INSPECTION_CREATED = "INSPECTION_CREATED"
INSPECTION_CONVERTED = "INSPECTION_CONVERTED"
CUSTODY_RECEIVED = "CUSTODY_RECEIVED"
CUSTODY_TRANSFERRED = "CUSTODY_TRANSFERRED"
CUSTODY_RELEASED = "CUSTODY_RELEASED"
CLAIM_DECIDED = "CLAIM_DECIDED"
HANDOVER_COMPLETED = "HANDOVER_COMPLETED"
USER_CREATED = "USER_CREATED"
MANAGER_ASSIGNED = "MANAGER_ASSIGNED"
MANAGER_REASSIGNED = "MANAGER_REASSIGNED"
MANAGER_REMOVED = "MANAGER_REMOVED"


def record_audit(actor_id, action, entity_type, entity_id=None, location_id=None, metadata=None):
    """Append an audit log entry. Called after the action has been committed.

    Never store passwords, OTPs, handover codes, tokens or ownership evidence
    in metadata.
    """
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        location_id=location_id,
        details=json.dumps(metadata) if metadata else None,
    )
    db.session.add(log)
    db.session.commit()
    return log


def serialize_audit_log(log):
    return {
        "id": log.id,
        "actor": serialize_user(log.actor) if log.actor else None,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "location_id": log.location_id,
        "metadata": json.loads(log.details) if log.details else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }
