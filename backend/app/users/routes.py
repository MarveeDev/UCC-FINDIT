from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.users import services as user_services
from app.users.models import UserRole
from app.utils import fail, ok
from app.utils.decorators import role_required

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = user_services.get_user_by_id(user_id)
    return ok(data=user_services.serialize_user(user))


@users_bp.get("")
@role_required(UserRole.SUPER_ADMIN)
def list_users():
    role = request.args.get("role")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    pagination = user_services.list_users(role, page, per_page)
    return ok(
        data={
            "items": [user_services.serialize_user(u) for u in pagination.items],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@users_bp.post("")
@role_required(UserRole.SUPER_ADMIN)
def create_user():
    data = request.get_json(silent=True) or {}
    user = user_services.create_user(
        data.get("first_name"),
        data.get("last_name"),
        data.get("email"),
        data.get("password"),
        data.get("role"),
    )
    return ok(data=user_services.serialize_user(user), status=201)
