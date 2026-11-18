from app.extensions import db
from app.users.models import utcnow


class InspectionStatus:
    OPEN = "OPEN"
    CONVERTED = "CONVERTED"


class Inspection(db.Model):
    __tablename__ = "inspections"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False, index=True)
    location_id = db.Column(
        db.Integer, db.ForeignKey("campus_locations.id"), nullable=False, index=True
    )
    staff_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspected_at = db.Column(db.DateTime, nullable=False)
    item_description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(64), nullable=False)
    colour = db.Column(db.String(40), nullable=True)
    brand = db.Column(db.String(80), nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    found_report_id = db.Column(
        db.Integer, db.ForeignKey("item_reports.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = db.Column(db.String(20), nullable=False, default=InspectionStatus.OPEN)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    staff = db.relationship("User")
    location = db.relationship("CampusLocation")

    def __repr__(self):
        return f"<Inspection {self.reference}>"
