from app.extensions import db
from app.users.models import utcnow


class RateLimitEvent(db.Model):
    __tablename__ = "rate_limit_events"
    __table_args__ = (
        db.Index("ix_rate_limit_action_key_created", "action", "key", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(64), nullable=False)
    key = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
