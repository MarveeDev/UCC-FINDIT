from app.extensions import db
from app.users.models import utcnow


class CampusLocation(db.Model):
    __tablename__ = "campus_locations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    managers = db.relationship(
        "LocationManager",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    staff_assignments = db.relationship(
        "StaffAssignment",
        back_populates="location",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<CampusLocation {self.name}>"


class LocationManager(db.Model):
    __tablename__ = "location_managers"
    __table_args__ = (
        db.UniqueConstraint("user_id", "location_id", name="uq_location_manager"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("campus_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User")
    location = db.relationship("CampusLocation", back_populates="managers")


class StaffAssignment(db.Model):
    __tablename__ = "staff_assignments"
    __table_args__ = (
        db.UniqueConstraint("user_id", "location_id", name="uq_staff_assignment"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    location_id = db.Column(
        db.Integer,
        db.ForeignKey("campus_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User")
    location = db.relationship("CampusLocation", back_populates="staff_assignments")
