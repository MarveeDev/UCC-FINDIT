import io

from tests.helpers import auth_header, create_user


def test_upload_rejects_non_image_extension(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b"hello"), "notes.txt")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_rejects_fake_image_content(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(b"not an image"), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_upload_image(client, tmp_path):
    client.application.config["UPLOAD_FOLDER"] = str(tmp_path)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 32
    resp = client.post(
        "/api/v1/uploads",
        data={"file": (io.BytesIO(png_bytes), "photo.png")},
        headers=headers,
        content_type="multipart/form-data",
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["url"].startswith("/api/v1/uploads/")
    assert data["filename"].endswith(".png")
    assert len(list(tmp_path.iterdir())) == 1
