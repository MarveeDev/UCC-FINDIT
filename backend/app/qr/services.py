import secrets

from app.extensions import db
from app.qr.models import QrRegistration
from app.utils import ApiError


def register_qr(owner, item_name, description):
    item_name = (item_name or "").strip()
    if not item_name:
        raise ApiError("Item name is required", status=422)
    if len(item_name) > 120:
        raise ApiError("Item name is too long", status=422)

    qr = QrRegistration(
        owner_id=owner.id,
        item_name=item_name,
        description=(description or "").strip() or None,
        token=secrets.token_urlsafe(24),
    )
    db.session.add(qr)
    db.session.commit()
    return qr


def get_qr(qr_id):
    qr = db.session.get(QrRegistration, qr_id)
    if qr is None:
        raise ApiError("QR registration not found", status=404)
    return qr


def get_by_token(token):
    return QrRegistration.query.filter_by(token=token).first()


def list_my_qr(owner):
    return (
        QrRegistration.query.filter_by(owner_id=owner.id)
        .order_by(QrRegistration.created_at.desc())
        .all()
    )


def deactivate_qr(owner, qr_id):
    qr = get_qr(qr_id)
    if qr.owner_id != owner.id:
        raise ApiError("You do not have permission to modify this QR code", status=403)
    qr.is_active = False
    db.session.commit()
    return qr


def serialize_qr(qr, include_token=False):
    """Privacy-protected serialization.

    The token and owner identity are only returned when the caller is the owner
    (include_token=True). A public lookup never exposes contact details.
    """
    data = {
        "id": qr.id,
        "item_name": qr.item_name,
        "description": qr.description,
        "is_active": qr.is_active,
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
    }
    if include_token:
        data["token"] = qr.token
        data["qr_url"] = f"/recover/{qr.token}"
    return data
