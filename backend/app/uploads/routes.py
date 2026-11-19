from io import BytesIO

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from PIL import Image, UnidentifiedImageError

from app.uploads.cloudinary_service import CloudinaryUploadError, upload_image
from app.utils import fail, ok

uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/v1/uploads")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


@uploads_bp.post("")
@jwt_required()
def upload_image_route():
    if "file" not in request.files:
        return fail("No file provided", status=422)

    file = request.files["file"]
    if file is None or file.filename == "":
        return fail("No file selected", status=422)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return fail("Only JPG, PNG, and WebP images are allowed", status=422)

    if file.mimetype not in ALLOWED_MIME_TYPES:
        return fail("Unsupported image type", status=422)

    data = file.read()
    if not data:
        return fail("Uploaded file is empty", status=422)
    if len(data) > MAX_IMAGE_BYTES:
        return fail("Image must be 5 MB or smaller", status=422)

    try:
        img = Image.open(BytesIO(data))
        detected_format = (img.format or "").lower()
        img.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return fail("Uploaded file is not a valid image", status=422)

    if detected_format not in {"jpeg", "png", "webp"}:
        return fail("Only JPG, PNG, and WebP images are allowed", status=422)

    try:
        url, public_id = upload_image(BytesIO(data))
    except CloudinaryUploadError:
        return fail("Image upload failed. Please try again.", status=502)

    return ok(data={"url": url, "public_id": public_id}, status=201)
