from app.extensions import db
from app.users.models import utcnow


class Match(db.Model):
    __tablename__ = "matches"
    __table_args__ = (
        db.UniqueConstraint("lost_report_id", "found_report_id", name="uq_match_pair"),
    )

    id = db.Column(db.Integer, primary_key=True)
    lost_report_id = db.Column(
        db.Integer,
        db.ForeignKey("item_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    found_report_id = db.Column(
        db.Integer,
        db.ForeignKey("item_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = db.Column(db.Integer, nullable=False)
    reasons = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    lost_report = db.relationship("ItemReport", foreign_keys=[lost_report_id])
    found_report = db.relationship("ItemReport", foreign_keys=[found_report_id])

    def __repr__(self):
        return f"<Match lost={self.lost_report_id} found={self.found_report_id} score={self.score}>"
