from tests.helpers import auth_header, create_user


def _manager_and_location(client, email="manager@ucc.edu.gh"):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]
    manager = create_user(email, "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )
    return admin, admin_headers, manager, auth_header(client, manager.email), loc


def _staff_payload(location_id, email="kofi@ucc.edu.gh"):
    return {
        "first_name": "Kofi",
        "last_name": "Asante",
        "email": email,
        "password": "Password1",
        "location_id": location_id,
    }


def test_manager_creates_staff(client):
    _, _, manager, manager_headers, loc = _manager_and_location(client)
    resp = client.post(
        "/api/v1/staff", json=_staff_payload(loc["id"]), headers=manager_headers
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["role"] == "LOCATION_STAFF"

    listing = client.get("/api/v1/staff", headers=manager_headers).get_json()["data"]
    assert any(s["user"]["email"] == "kofi@ucc.edu.gh" for s in listing)


def test_manager_cannot_assign_staff_to_unmanaged_location(client):
    _, admin_headers, manager, manager_headers, loc = _manager_and_location(client)
    other = client.post(
        "/api/v1/locations", json={"name": "Other Lab"}, headers=admin_headers
    ).get_json()["data"]
    resp = client.post(
        "/api/v1/staff", json=_staff_payload(other["id"]), headers=manager_headers
    )
    assert resp.status_code == 403


def test_staff_cannot_manage_staff(client):
    staff = create_user("staff@ucc.edu.gh", "LOCATION_STAFF")
    headers = auth_header(client, staff.email)
    assert client.get("/api/v1/staff", headers=headers).status_code == 403


def test_remove_staff_assignment(client):
    _, _, manager, manager_headers, loc = _manager_and_location(client)
    staff = client.post(
        "/api/v1/staff", json=_staff_payload(loc["id"]), headers=manager_headers
    ).get_json()["data"]

    resp = client.delete(
        f"/api/v1/staff/{staff['id']}/assignments/{loc['id']}", headers=manager_headers
    )
    assert resp.status_code == 200

    listing = client.get("/api/v1/staff", headers=manager_headers).get_json()["data"]
    assert not any(s["user"]["id"] == staff["id"] for s in listing)


def test_admin_creates_user_and_lists(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    headers = auth_header(client, admin.email)
    resp = client.post(
        "/api/v1/users",
        json={
            "first_name": "Manager",
            "last_name": "One",
            "email": "m1@ucc.edu.gh",
            "password": "Password1",
            "role": "LOCATION_MANAGER",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    listing = client.get("/api/v1/users?role=LOCATION_MANAGER", headers=headers).get_json()["data"]
    assert any(u["email"] == "m1@ucc.edu.gh" for u in listing["items"])


def test_student_cannot_create_user(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/users",
        json={"first_name": "X", "last_name": "Y", "email": "x@ucc.edu.gh",
              "password": "Password1", "role": "LOCATION_STAFF"},
        headers=headers,
    )
    assert resp.status_code == 403


def test_manager_cannot_view_out_of_scope_staff_activity(client):
    _, admin_headers, _, manager_headers, _ = _manager_and_location(client)
    other_loc = client.post(
        "/api/v1/locations", json={"name": "Other Lab"}, headers=admin_headers
    ).get_json()["data"]
    other_manager = create_user("othermgr@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{other_loc['id']}/managers",
        json={"user_id": other_manager.id},
        headers=admin_headers,
    )
    other_manager_headers = auth_header(client, other_manager.email)
    other_staff = client.post(
        "/api/v1/staff",
        json=_staff_payload(other_loc["id"], "otherstaff@ucc.edu.gh"),
        headers=other_manager_headers,
    ).get_json()["data"]

    resp = client.get(
        f"/api/v1/staff/{other_staff['id']}/activity", headers=manager_headers
    )
    assert resp.status_code == 403
