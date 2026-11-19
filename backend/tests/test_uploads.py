import io

from PIL import Image

from tests.helpers import auth_header, create_user


def _png_bytes(size=(8, 8)):
    buf = io.BytesIO()
    Image.new("RGB", size, (255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _configure_cloudinary(client, monkeypatch):
    client.application.config["CLOUDINARY_CLOUD_NAME"] = "test-cloud"
    client.application.config["CLOUDINARY_API_KEY"] = "test-key"
    client.application.config["CLOUDINARY_API_SECRET"] = "test-secret"


def _student_headers(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    return auth_header(client, student.email)


def test_upload_requires_auth(client):
    resp = client.post("/api/v1/uploads", data={"file": (io.BytesIO(b"x"), "x.png")})
    assert resp.status_code == 401


def test_upload_rejects_non_image_extension(client):
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b"hello"), "notes.txt")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_rejects_svg(client):
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b"<svg></svg>"), "image.svg")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_rejects_fake_image_content(client):
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b"not an image"), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_rejects_empty_file(client):
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b""), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_rejects_oversized_file(client):
    headers = _student_headers(client)
    big = b"x" * (5 * 1024 * 1024 + 1)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(big), "big.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_image(client, monkeypatch):
    _configure_cloudinary(client, monkeypatch)
    monkeypatch.setattr(
        "cloudinary.uploader.upload",
        lambda *a, **kw: {
            "secure_url": "https://res.cloudinary.com/test-cloud/image/upload/v1/ucc-findit/items/abc123.png",
            "public_id": "ucc-findit/items/abc123",
        },
    )
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(_png_bytes()), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["url"].startswith("https://res.cloudinary.com/")
    assert data["public_id"].startswith("ucc-findit/items/")


def test_upload_returns_502_when_cloudinary_unconfigured(client):
    headers = _student_headers(client)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(_png_bytes()), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 502
