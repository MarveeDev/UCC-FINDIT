from datetime import datetime, timezone

from app.extensions import db


def utcnow():
    """Return the current UTC time as a naive datetime.

    Storing naive UTC keeps behaviour consistent across PostgreSQL and SQLite.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRole:
    STUDENT = "STUDENT"
    LOCATION_STAFF = "LOCATION_STAFF"
    LOCATION_MANAGER = "LOCATION_MANAGER"
    SUPER_ADMIN = "SUPER_ADMIN"

    ALL = {STUDENT, LOCATION_STAFF, LOCATION_MANAGER, SUPER_ADMIN}


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(32), nullable=False, default=UserRole.STUDENT)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"
