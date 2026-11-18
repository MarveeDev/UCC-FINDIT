from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.utils import fail


def role_required(*roles):
    """Restrict an endpoint to one or more user roles.

    The caller must already be authenticated; the role is read from the JWT
    claims and never trusted from the request body.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return fail(
                    "You do not have permission to perform this action", status=403
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
