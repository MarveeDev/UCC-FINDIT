from app.extensions import db
from app.locations.services import responsible_manager_ids
from app.notifications.models import Notification, NotificationType
from app.utils import ApiError


def notify_location_managers(report):
    """Create a notification for each manager responsible for a report's location.

    Returns the created notifications. Locations without an assigned manager
    are handled explicitly (no notification is created) rather than silently
    losing the event; the report still appears in the campus-wide feed.
    """
    manager_ids = responsible_manager_ids(report.location_id)
    if not manager_ids:
        return []

    location_name = report.location.name if report.location else "the campus"
    report_type = report.report_type.lower()
    title = f"New {report_type} report at {location_name}"
    message = f"{report.item_name} ({report.category}) was reported at {location_name}."

    created = []
    for user_id in manager_ids:
        notification = Notification(
            user_id=user_id,
            type=NotificationType.NEW_REPORT,
            title=title,
            message=message,
            report_id=report.id,
        )
        db.session.add(notification)
        created.append(notification)
    db.session.commit()
    return created


def serialize_notification(notification):
    return {
        "id": notification.id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "report_id": notification.report_id,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat() if notification.created_at else None,
    }


def list_notifications(user_id, page, per_page):
    query = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    )
    return query.paginate(page=page, per_page=per_page, error_out=False)


def unread_count(user_id):
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()


def mark_read(user_id, notification_id):
    notification = Notification.query.filter_by(
        id=notification_id, user_id=user_id
    ).first()
    if notification is None:
        raise ApiError("Notification not found", status=404)
    notification.is_read = True
    db.session.commit()
    return notification


def mark_all_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
