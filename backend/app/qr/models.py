from app.extensions import db
from app.users.models import utcnow


class QrRegistration(db.Model):
    __tablename__ = "qr_registrations"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    owner = db.relationship("User")

    def __repr__(self):
        return f"<QrRegistration #{self.id} {self.item_name}>"
