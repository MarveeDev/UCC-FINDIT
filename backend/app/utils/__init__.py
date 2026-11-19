from flask import jsonify
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    """Raised by services to signal a typed HTTP error response."""

    def __init__(self, message, status=400, errors=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors


def ok(data=None, message=None, status=200, **extra):
    """Return a consistent success envelope."""
    payload = {"success": True}
    if data is not None:
        payload["data"] = data
    if message is not None:
        payload["message"] = message
    payload.update(extra)
    return jsonify(payload), status


def fail(message, status=400, errors=None, **extra):
    """Return a consistent error envelope."""
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    payload.update(extra)
    return jsonify(payload), status


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return fail(error.message, status=error.status, errors=error.errors)

    @app.errorhandler(404)
    def handle_not_found(_error):
        return fail("Resource not found", status=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return fail("Method not allowed", status=405)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return fail(error.name, status=error.code)

    @app.errorhandler(OperationalError)
    def handle_db_operational_error(error):
        # Log the connection error type (not secrets or SQL) for diagnostics
        # and return a safe, retryable message to the client.
        app.logger.error("Database connection error: %s", type(error).__name__)
        return fail(
            "Service temporarily unavailable. Please try again later.", status=503
        )

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        app.logger.exception("Unhandled server error: %s", error)
        return fail("An unexpected error occurred", status=500)
