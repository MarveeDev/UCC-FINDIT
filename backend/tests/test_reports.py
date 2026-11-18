from datetime import date

from tests.helpers import auth_header, create_user


def _create_location(client, admin_headers, name="Main Library"):
    return client.post(
        "/api/v1/locations", json={"name": name}, headers=admin_headers
    ).get_json()["data"]


def _report_payload(location_id, **overrides):
    payload = {
        "report_type": "LOST",
        "item_name": "Black Laptop",
        "category": "Electronics",
        "description": "Dell XPS 13 in a black sleeve",
        "brand": "Dell",
        "colour": "Black",
        "location_id": location_id,
        "event_date": date.today().isoformat(),
    }
    payload.update(overrides)
    return payload


def _admin_and_location(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = _create_location(client, admin_headers)
    return admin, admin_headers, loc


def test_create_lost_report_is_privacy_safe(client):
    _, admin_headers, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(loc["id"], identifying_characteristics="Scratch on lid"),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["report_type"] == "LOST"
    assert data["item_name"] == "Black Laptop"
    assert data["location_name"] == "Main Library"
    assert data["status"] == "OPEN"
    assert "identifying_characteristics" not in data
    assert "custody_info" not in data
    assert data["reporter_name"]


def test_report_validation_errors(client):
    _, admin_headers, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports",
        json={"report_type": "LOST", "location_id": loc["id"]},
        headers=headers,
    )
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    assert "item_name" in errors
    assert "category" in errors
    assert "description" in errors


def test_report_rejects_invalid_category(client):
    _, admin_headers, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports",
        json=_report_payload(loc["id"], category="NotARealCategory"),
        headers=headers,
    )
    assert resp.status_code == 422
    assert "category" in resp.get_json()["errors"]


def test_report_rejects_invalid_location(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/reports", json=_report_payload(9999), headers=headers
    )
    assert resp.status_code == 400


def test_report_detail_requires_auth(client):
    _, admin_headers, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    report_id = client.post(
        "/api/v1/reports", json=_report_payload(loc["id"]), headers=headers
    ).get_json()["data"]["id"]

    assert client.get(f"/api/v1/reports/{report_id}").status_code == 401

    resp = client.get(f"/api/v1/reports/{report_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["id"] == report_id
