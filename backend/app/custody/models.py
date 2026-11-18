from app.extensions import db
from app.users.models import utcnow


class CustodyEventType:
    RECEIVED = "RECEIVED"
    TRANSFERRED = "TRANSFERRED"
    RELEASED = "RELEASED"


class CustodyRecord(db.Model):
    __tablename__ = "custody_records"

    id = db.Column(db.Integer, primary_key=True)
    found_report_id = db.Column(
        db.Integer, db.ForeignKey("item_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = db.Column(db.String(20), nullable=False)
    staff_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location_id = db.Column(
        db.Integer, db.ForeignKey("campus_locations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    authorized_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    staff = db.relationship("User", foreign_keys=[staff_id])
    authorizer = db.relationship("User", foreign_keys=[authorized_by])
    location = db.relationship("CampusLocation")

    def __repr__(self):
        return f"<CustodyRecord {self.event_type} report={self.found_report_id}>"
