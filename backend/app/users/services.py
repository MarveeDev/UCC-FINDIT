from werkzeug.security import generate_password_hash

from app.extensions import db
from app.users.models import User, UserRole
from app.utils import ApiError


def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise ApiError("User not found", status=404)
    return user


def get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def create_user(first_name, last_name, email, password, role):
    """Create a provisioned account (used by super admin / managers)."""
    from app.auth.validators import normalize_email, validate_password

    if role not in UserRole.ALL:
        raise ApiError("Invalid role", status=422)
    email = normalize_email(email)
    if not email:
        raise ApiError("A valid email address is required", status=422)
    if User.query.filter_by(email=email).first():
        raise ApiError("A user with this email already exists", status=409)

    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    if not first_name or not last_name:
        raise ApiError("First and last name are required", status=422)

    password_error = validate_password(password)
    if password_error:
        raise ApiError(password_error, status=422)

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def list_users(role=None, page=1, per_page=20):
    query = User.query
    if role:
        query = query.filter_by(role=role)
    return query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )


def serialize_user(user):
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
