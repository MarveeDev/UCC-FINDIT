import os
import uuid

from flask import Blueprint, current_app, request, send_from_directory
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from app.utils import fail, ok

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/v1/uploads")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def _allowed_extension(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
    )


def _looks_like_image(stream):
    header = stream.read(16)
    stream.seek(0)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if header.startswith(b"\xff\xd8\xff"):
        return True
    if header.startswith((b"GIF87a", b"GIF89a")):
        return True
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return True
    return False


@uploads_bp.post("")
@jwt_required()
def upload_image():
    if "file" not in request.files:
        return fail("No file provided", status=422)
    file = request.files["file"]
    if file is None or file.filename == "":
        return fail("No file selected", status=422)
    if not _allowed_extension(file.filename):
        return fail(
            "Only image files (png, jpg, jpeg, webp, gif) are allowed", status=422
        )
    if not _looks_like_image(file.stream):
        return fail("Uploaded file is not a valid image", status=422)

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    return ok(
        data={"filename": filename, "url": f"/api/v1/uploads/{filename}"},
        status=201,
    )


@uploads_bp.get("/<path:filename>")
def serve_upload(filename):
    # Image URLs use unguessable UUID filenames; only the sanitized basename is
    # ever served from the upload directory.
    safe = secure_filename(filename)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], safe)
