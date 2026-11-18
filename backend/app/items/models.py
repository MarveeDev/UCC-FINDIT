from app.extensions import db
from app.users.models import utcnow


class ReportType:
    LOST = "LOST"
    FOUND = "FOUND"
    ALL = {LOST, FOUND}


class ItemStatus:
    OPEN = "OPEN"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    CLAIM_PENDING = "CLAIM_PENDING"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    APPROVED_FOR_COLLECTION = "APPROVED_FOR_COLLECTION"
    RECOVERED = "RECOVERED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"

    ALL = {
        OPEN,
        POSSIBLE_MATCH,
        CLAIM_PENDING,
        VERIFICATION_REQUIRED,
        APPROVED_FOR_COLLECTION,
        RECOVERED,
        REJECTED,
        CLOSED,
    }


ITEM_CATEGORIES = [
    "Electronics",
    "Clothing",
    "Books & Documents",
    "Keys",
    "Bags & Luggage",
    "IDs & Cards",
    "Jewellery",
    "Water Bottles",
    "Other",
]


class ItemReport(db.Model):
    __tablename__ = "item_reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type = db.Column(db.String(10), nullable=False)
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=False)
    brand = db.Column(db.String(80), nullable=True)
    colour = db.Column(db.String(40), nullable=True)
    identifying_characteristics = db.Column(db.Text, nullable=True)
    location_id = db.Column(
        db.Integer, db.ForeignKey("campus_locations.id"), nullable=False, index=True
    )
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.Time, nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    custody_info = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default=ItemStatus.OPEN)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    reporter = db.relationship("User")
    location = db.relationship("CampusLocation")

    def __repr__(self):
        return f"<ItemReport {self.report_type} #{self.id} {self.item_name}>"
