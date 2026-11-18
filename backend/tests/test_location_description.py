from datetime import date

from tests.helpers import auth_header, create_user


def _admin_and_location(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]
    return admin, admin_headers, loc


def _base_payload(**overrides):
    payload = {
        "report_type": "LOST",
        "item_name": "Black Laptop",
        "category": "Electronics",
        "description": "Dell XPS 13",
        "location_description": "Behind the Science Building",
        "event_date": date.today().isoformat(),
    }
    payload.update(overrides)
    return payload


def test_free_text_location_only(client):
    _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post("/api/v1/reports", json=_base_payload(), headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["location_description"] == "Behind the Science Building"
    assert data["location_id"] is None
    assert data["location_name"] is None


def test_free_text_plus_registered_location(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports", json=_base_payload(location_id=loc["id"]), headers=headers
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["location_description"] == "Behind the Science Building"
    assert data["location_id"] == loc["id"]
    assert data["location_name"] == "Main Library"


def test_free_text_plus_coordinates(client):
    _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports",
        json=_base_payload(latitude=5.1155, longitude=-1.2909),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["latitude"] == 5.1155
    assert data["location_id"] is None


def test_all_three(client):
    _, _, loc = _admin_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    resp = client.post(
        "/api/v1/reports",
        json=_base_payload(location_id=loc["id"], latitude=5.1155, longitude=-1.2909),
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["location_id"] == loc["id"]
    assert data["latitude"] == 5.1155


def test_empty_location_description_rejected(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/reports", json=_base_payload(location_description="   "), headers=headers
    )
    assert resp.status_code == 422
    assert "location_description" in resp.get_json()["errors"]


def test_missing_location_description_rejected(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    payload = _base_payload()
    payload.pop("location_description")
    resp = client.post("/api/v1/reports", json=payload, headers=headers)
    assert resp.status_code == 422
    assert "location_description" in resp.get_json()["errors"]


def test_free_text_report_does_not_notify_manager(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    resp = client.post("/api/v1/reports", json=_base_payload(), headers=student_headers)
    assert resp.status_code == 201

    manager_headers = auth_header(client, manager.email)
    unread = client.get("/api/v1/notifications/unread-count", headers=manager_headers)
    assert unread.get_json()["data"]["count"] == 0
