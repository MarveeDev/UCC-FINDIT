"""Cloudinary object-storage service.

Centralises Cloudinary configuration, image upload, deletion, and error
handling. Credentials are read from the Flask application configuration and
never hardcoded or logged.
"""

import logging
import uuid

import cloudinary
import cloudinary.uploader
from flask import current_app

logger = logging.getLogger(__name__)


class CloudinaryUploadError(Exception):
    """Raised when an image cannot be uploaded to or removed from Cloudinary."""


def _is_configured():
    return all(
        current_app.config.get(key)
        for key in (
            "CLOUDINARY_CLOUD_NAME",
            "CLOUDINARY_API_KEY",
            "CLOUDINARY_API_SECRET",
        )
    )


def _configure():
    cloudinary.config(
        cloud_name=current_app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=current_app.config["CLOUDINARY_API_KEY"],
        api_secret=current_app.config["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_image(file_obj):
    """Upload an image file-like object to Cloudinary.

    Returns a ``(secure_url, public_id)`` tuple. Raises CloudinaryUploadError
    when Cloudinary is not configured or the upload fails.
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
