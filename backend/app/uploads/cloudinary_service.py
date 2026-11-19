"""Cloudinary object-storage service.

Centralises Cloudinary configuration, image upload, deletion, credential
verification, and error handling. Credentials are read from the Flask
application configuration and never hardcoded or logged.
"""

import logging
import uuid

import cloudinary
import cloudinary.api
import cloudinary.uploader
from cloudinary.exceptions import AuthorizationRequired
from flask import current_app

logger = logging.getLogger(__name__)

# Keys the Cloudinary SDK reads from the environment on import. Kept explicit so
# diagnostics can describe the configuration source without leaking values.
_CONFIG_KEYS = (
    "CLOUDINARY_CLOUD_NAME",
    "CLOUDINARY_API_KEY",
    "CLOUDINARY_API_SECRET",
)


class CloudinaryUploadError(Exception):
    """Raised when an image cannot be uploaded to or removed from Cloudinary."""


class CloudinaryAuthError(CloudinaryUploadError):
    """Raised when Cloudinary rejects the configured credentials (HTTP 401)."""


def _is_configured():
    return all(current_app.config.get(key) for key in _CONFIG_KEYS)


def _configure():
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def diagnostics():
    """Return sanitized configuration diagnostics (never secret values)."""
    def _summarize(key):
        value = current_app.config.get(key) or ""
        return {"present": bool(value), "length": len(value)}

    return {
        "cloud_name": _summarize("CLOUDINARY_CLOUD_NAME"),
        "api_key": _summarize("CLOUDINARY_API_KEY"),
        "api_secret": _summarize("CLOUDINARY_API_SECRET"),
        "folder": current_app.config.get("CLOUDINARY_FOLDER", "ucc-findit/items"),
        "configured": _is_configured(),
    }


def verify_credentials():
    """Verify credentials using Cloudinary's lightweight ping API (no upload).

    Returns a ``(ok, detail)`` tuple. ``detail`` is a safe, sanitized string.
    """
    if not _is_configured():
        return False, "missing_configuration"

    try:
        _configure()
        result = cloudinary.api.ping()
    except AuthorizationRequired:
        return False, "authorization_required"
    except Exception as exc:
        return False, type(exc).__name__

    return result.get("status") == "ok", "ok"


def upload_image(file_obj):
    """Upload an image file-like object to Cloudinary.

    Returns a ``(secure_url, public_id)`` tuple. Raises CloudinaryAuthError when
    the credentials are rejected, and CloudinaryUploadError for other failures.
    """
    if not _is_configured():
        raise CloudinaryUploadError("Image storage is not configured")

    folder = current_app.config.get("CLOUDINARY_FOLDER", "ucc-findit/items")
    public_id = f"{folder}/{uuid.uuid4().hex}"

    try:
        _configure()
        result = cloudinary.uploader.upload(
            file_obj,
            public_id=public_id,
            resource_type="image",
        )
    except AuthorizationRequired as exc:
        logger.error("Cloudinary authorization failed (check API key/secret)")
        raise CloudinaryAuthError("Image storage is not authorized") from exc
    except Exception as exc:
        logger.error("Cloudinary upload failed (%s)", type(exc).__name__)
        raise CloudinaryUploadError("Image upload failed") from exc

    return result.get("secure_url"), result.get("public_id")


def delete_image(public_id):
    """Delete an image from Cloudinary by public ID.

    Returns True when the deletion was acknowledged. Never raises; failures are
    logged and reported as False so callers can decide how to proceed.
    """
    if not public_id or not _is_configured():
        return False
    try:
        _configure()
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
    except Exception as exc:
        logger.error("Cloudinary delete failed (%s)", type(exc).__name__)
        return False
    return result.get("result") == "ok"
