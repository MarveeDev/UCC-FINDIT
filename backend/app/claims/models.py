from app.extensions import db
from app.users.models import utcnow


class ClaimStatus:
    PENDING = "PENDING"
    MORE_INFORMATION_REQUIRED = "MORE_INFORMATION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    ALL = {PENDING, MORE_INFORMATION_REQUIRED, APPROVED, REJECTED}


class OwnershipClaim(db.Model):
    __tablename__ = "ownership_claims"
    __table_args__ = (
        db.UniqueConstraint("report_id", "claimant_id", name="uq_claim_report_claimant"),
        # Database-level guarantee that only one claim per item can be approved.
        db.Index(
            "uq_one_approved_claim_per_report",
            "report_id",
            unique=True,
            postgresql_where=db.text("status = 'APPROVED'"),
            sqlite_where=db.text("status = 'APPROVED'"),
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(
        db.Integer, db.ForeignKey("item_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claimant_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default=ClaimStatus.PENDING)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    review_note = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    report = db.relationship("ItemReport")
    claimant = db.relationship("User", foreign_keys=[claimant_id])
    reviewer = db.relationship("User", foreign_keys=[reviewer_id])

    handover_codes = db.relationship(
        "HandoverCode", back_populates="claim", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self):
        return f"<OwnershipClaim #{self.id} report={self.report_id} status={self.status}>"


class HandoverCode(db.Model):
    __tablename__ = "handover_codes"

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(
        db.Integer, db.ForeignKey("ownership_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Hashed value of the one-time collection code. The plaintext is returned
    # only at generation time (to the approving manager) and is never stored,
    # so it cannot be recovered later.
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    is_consumed = db.Column(db.Boolean, nullable=False, default=False)
    consumed_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    claim = db.relationship("OwnershipClaim", back_populates="handover_codes")
    verifier = db.relationship("User", foreign_keys=[verified_by])
