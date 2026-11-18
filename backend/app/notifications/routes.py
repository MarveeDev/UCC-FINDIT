from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.notifications import services as notification_services
from app.utils import ok

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")


@notifications_bp.get("")
@jwt_required()
def list_notifications():
    user_id = int(get_jwt_identity())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    pagination = notification_services.list_notifications(user_id, page, per_page)
    return ok(
        data={
            "items": [
                notification_services.serialize_notification(n)
                for n in pagination.items
            ],
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
        }
    )


@notifications_bp.get("/unread-count")
@jwt_required()
def unread_count():
    count = notification_services.unread_count(int(get_jwt_identity()))
    return ok(data={"count": count})


@notifications_bp.patch("/read-all")
@jwt_required()
def read_all():
    notification_services.mark_all_read(int(get_jwt_identity()))
    return ok(message="All notifications marked as read")


@notifications_bp.patch("/<int:notification_id>/read")
@jwt_required()
def read_one(notification_id):
    notification = notification_services.mark_read(
        int(get_jwt_identity()), notification_id
    )
    return ok(data=notification_services.serialize_notification(notification))
