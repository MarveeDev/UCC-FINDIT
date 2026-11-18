from tests.helpers import auth_header, create_user


def _manager_and_location(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]
    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )
    manager_headers = auth_header(client, manager.email)
    staff = create_user("staff@ucc.edu.gh", "LOCATION_STAFF")
    client.post(
        f"/api/v1/locations/{loc['id']}/staff",
        json={"user_id": staff.id},
        headers=manager_headers,
    )
    staff_headers = auth_header(client, staff.email)
    return admin_headers, manager_headers, staff_headers, loc


def _inspection_payload(location_id, **overrides):
    payload = {
        "location_id": location_id,
        "item_description": "A blue water bottle found under a desk",
        "category": "Water Bottles",
        "notes": "Found during morning inspection",
    }
    payload.update(overrides)
    return payload


def test_staff_creates_inspection(client):
    _, _, staff_headers, loc = _manager_and_location(client)
    resp = client.post(
        "/api/v1/inspections", json=_inspection_payload(loc["id"]), headers=staff_headers
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["reference"].startswith("INS-")
    assert data["status"] == "OPEN"
    assert data["location_name"] == "Main Library"


def test_staff_cannot_inspect_unassigned_location(client):
    _, _, _, loc = _manager_and_location(client)
    other_admin = create_user("admin2@ucc.edu.gh", "SUPER_ADMIN")
    other_admin_headers = auth_header(client, other_admin.email)
    other = client.post(
        "/api/v1/locations", json={"name": "Other Lab"}, headers=other_admin_headers
    ).get_json()["data"]

    outsider = create_user("outsider@ucc.edu.gh", "LOCATION_STAFF")
    outsider_headers = auth_header(client, outsider.email)
    resp = client.post(
        "/api/v1/inspections", json=_inspection_payload(other["id"]), headers=outsider_headers
    )
    assert resp.status_code == 403


def test_inspection_convert_creates_found_report(client):
    _, _, staff_headers, loc = _manager_and_location(client)
    inspection = client.post(
        "/api/v1/inspections", json=_inspection_payload(loc["id"]), headers=staff_headers
    ).get_json()["data"]

    resp = client.post(
        f"/api/v1/inspections/{inspection['id']}/convert", headers=staff_headers
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["inspection"]["status"] == "CONVERTED"
    assert data["inspection"]["found_report_id"] == data["report"]["id"]
    assert data["report"]["report_type"] == "FOUND"


def test_inspection_convert_prevents_duplicate(client):
    _, _, staff_headers, loc = _manager_and_location(client)
    inspection = client.post(
        "/api/v1/inspections", json=_inspection_payload(loc["id"]), headers=staff_headers
    ).get_json()["data"]

    assert (
        client.post(
            f"/api/v1/inspections/{inspection['id']}/convert", headers=staff_headers
        ).status_code
        == 200
    )
    resp = client.post(
        f"/api/v1/inspections/{inspection['id']}/convert", headers=staff_headers
    )
    assert resp.status_code == 409


def test_manager_sees_location_inspections(client):
    _, manager_headers, staff_headers, loc = _manager_and_location(client)
    client.post(
        "/api/v1/inspections", json=_inspection_payload(loc["id"]), headers=staff_headers
    )
    listing = client.get("/api/v1/inspections", headers=manager_headers).get_json()["data"]
    assert len(listing) == 1
    assert listing[0]["location_id"] == loc["id"]
