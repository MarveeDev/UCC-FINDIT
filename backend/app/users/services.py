from app.extensions import db
from app.users.models import User
from app.utils import ApiError


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("User not found", status=404)
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def serialize_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "email_verified": user.email_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
