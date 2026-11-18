from app.extensions import db
from app.users.models import utcnow


class NotificationType:
    NEW_REPORT = "NEW_REPORT"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    CLAIM_SUBMITTED = "CLAIM_SUBMITTED"
    CLAIM_APPROVED = "CLAIM_APPROVED"
    CLAIM_REJECTED = "CLAIM_REJECTED"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    HANDOVER_READY = "HANDOVER_READY"
    RECOVERY_COMPLETED = "RECOVERY_COMPLETED"
    SECURITY_ALERT = "SECURITY_ALERT"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    report_id = db.Column(
        db.Integer,
        db.ForeignKey("item_reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    recipient = db.relationship("User")
