from datetime import timedelta

from flask import request

from app.extensions import db
from app.security.models import RateLimitEvent
from app.users.models import utcnow
from app.utils import ApiError


def enforce_rate_limit(action, key, limit, window_seconds):
    """Reject when the number of recent events meets the limit, then record
    this attempt.

    DB-backed so it works across multiple workers without Redis. Keyed by IP
    (or another caller-supplied identifier) over a sliding time window.
    """
    window_start = utcnow() - timedelta(seconds=window_seconds)
    count = (
        RateLimitEvent.query.filter(
            RateLimitEvent.action == action,
            RateLimitEvent.key == key,
            RateLimitEvent.created_at >= window_start,
        ).count()
    )
    if count >= limit:
        raise ApiError("Too many requests. Please try again later.", status=429)

    db.session.add(RateLimitEvent(action=action, key=key))
    db.session.commit()


def client_ip():
    return request.remote_addr or "unknown"
