from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.users.models import User
from app.users.services import serialize_user
from app.utils import ApiError


def register_user(first_name, last_name, email, password):
    if get_user(email):
        raise ApiError("An account with this email already exists", status=409)

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()

    return {
        "user": serialize_user(user),
        "message": "Account created successfully. You can now sign in.",
    }


def get_user(email):
    return User.query.filter_by(email=email).first()


def login(email, password):
    user = get_user(email)
    if user is None or not check_password_hash(user.password_hash, password):
        raise ApiError("Invalid email or password", status=401)
    if not user.is_active:
        raise ApiError("This account has been deactivated", status=403)
    return {"user": serialize_user(user), "access_token": create_token(user)}


def create_token(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email},
    )
