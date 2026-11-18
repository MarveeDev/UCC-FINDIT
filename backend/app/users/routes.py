from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.users import services as user_services
from app.utils import ok

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_bp.get("/me")
@jwt_required()
def me():
    user_id = int(get_jwt_identity())
    user = user_services.get_user_by_id(user_id)
    return ok(data=user_services.serialize_user(user))
