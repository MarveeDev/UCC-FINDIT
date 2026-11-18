from datetime import date

from tests.helpers import auth_header, create_user


def _admin_and_location(client, name="Main Library", **coords):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": name, **coords}, headers=admin_headers
    ).get_json()["data"]
    return admin, admin_headers, loc


def _report(client, headers, location_id, **extra):
    payload = {
        "report_type": "LOST",
        "item_name": "Phone",
        "category": "Electronics",
        "description": "A phone",
        "location_id": location_id,
        "location_description": "Near the campus library",
        "event_date": date.today().isoformat(),
        **extra,
    }
    return client.post("/api/v1/reports", json=payload, headers=headers)


def test_report_accepts_valid_coordinates(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"], latitude=5.1155, longitude=-1.2909)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["latitude"] == 5.1155
    assert data["longitude"] == -1.2909


def test_report_rejects_out_of_range_latitude(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"], latitude=95, longitude=-1.29)
    assert resp.status_code == 422
    assert "latitude" in resp.get_json()["errors"]


def test_report_rejects_out_of_range_longitude(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"], latitude=5.1, longitude=200)
    assert resp.status_code == 422
    assert "longitude" in resp.get_json()["errors"]


def test_report_requires_both_coordinates(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"], latitude=5.1)
    assert resp.status_code == 422
    assert "latitude" in resp.get_json()["errors"]


def test_report_without_coordinates_still_valid(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"])
    assert resp.status_code == 201
    assert resp.get_json()["data"]["latitude"] is None


def test_report_inherits_location_fallback_coordinates(client):
    _, _, loc = _admin_and_location(client, latitude=5.1, longitude=-1.2)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = _report(client, headers, loc["id"])
    data = resp.get_json()["data"]
    assert data["latitude"] is None
    assert data["location_latitude"] == 5.1
    assert data["location_longitude"] == -1.2


def test_location_accepts_and_serializes_coordinates(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    headers = auth_header(client, admin.email)
    resp = client.post(
        "/api/v1/locations",
        json={"name": "Auditorium 900", "latitude": 5.1155, "longitude": -1.2909},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["latitude"] == 5.1155
    assert data["longitude"] == -1.2909


def test_location_rejects_invalid_coordinates(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    headers = auth_header(client, admin.email)
    resp = client.post(
        "/api/v1/locations",
        json={"name": "Bad Lab", "latitude": 100, "longitude": 0},
        headers=headers,
    )
    assert resp.status_code == 422


def test_location_update_coordinates(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Library"}, headers=headers
    ).get_json()["data"]

    resp = client.patch(
        f"/api/v1/locations/{loc['id']}",
        json={"latitude": 5.1155, "longitude": -1.2909},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["latitude"] == 5.1155
