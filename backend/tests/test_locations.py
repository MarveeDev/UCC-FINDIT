from tests.helpers import auth_header, create_user


def test_create_and_list_locations(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)

    resp = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Main Library"

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    listing = client.get("/api/v1/locations", headers=student_headers)
    assert listing.status_code == 200
    names = [loc["name"] for loc in listing.get_json()["data"]]
    assert "Main Library" in names


def test_student_cannot_create_location(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/locations", json={"name": "Auditorium"}, headers=headers
    )
    assert resp.status_code == 403


def test_duplicate_location_name_rejected(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    headers = auth_header(client, admin.email)
    assert (
        client.post("/api/v1/locations", json={"name": "Hostel"}, headers=headers).status_code
        == 201
    )
    resp = client.post("/api/v1/locations", json={"name": "Hostel"}, headers=headers)
    assert resp.status_code == 409


def test_assign_manager_and_staff(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Science Theatre"}, headers=admin_headers
    ).get_json()["data"]

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    resp = client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )
    assert resp.status_code == 201

    staff = create_user("staff@ucc.edu.gh", "LOCATION_STAFF")
    manager_headers = auth_header(client, manager.email)
    resp = client.post(
        f"/api/v1/locations/{loc['id']}/staff",
        json={"user_id": staff.id},
        headers=manager_headers,
    )
    assert resp.status_code == 201

    managers = client.get(
        f"/api/v1/locations/{loc['id']}/managers", headers=admin_headers
    ).get_json()["data"]
    assert any(m["id"] == manager.id for m in managers)


def test_student_cannot_assign_staff(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Hostel"}, headers=admin_headers
    ).get_json()["data"]

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    resp = client.post(
        f"/api/v1/locations/{loc['id']}/staff",
        json={"user_id": student.id},
        headers=student_headers,
    )
    assert resp.status_code == 403


def test_deactivate_location_hides_from_listing(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Old Lab"}, headers=admin_headers
    ).get_json()["data"]

    resp = client.delete(f"/api/v1/locations/{loc['id']}", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_active"] is False

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    names = [
        l["name"]
        for l in client.get("/api/v1/locations", headers=student_headers).get_json()["data"]
    ]
    assert "Old Lab" not in names


def test_manager_reassignment_moves_to_single_theatre(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc_a = client.post(
        "/api/v1/locations", json={"name": "Theatre A"}, headers=admin_headers
    ).get_json()["data"]
    loc_b = client.post(
        "/api/v1/locations", json={"name": "Theatre B"}, headers=admin_headers
    ).get_json()["data"]

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    assert (
        client.post(
            f"/api/v1/locations/{loc_a['id']}/managers",
            json={"user_id": manager.id},
            headers=admin_headers,
        ).status_code
        == 201
    )
    # Reassigning to theatre B atomically revokes theatre A.
    assert (
        client.post(
            f"/api/v1/locations/{loc_b['id']}/managers",
            json={"user_id": manager.id},
            headers=admin_headers,
        ).status_code
        == 201
    )

    managers_a = client.get(
        f"/api/v1/locations/{loc_a['id']}/managers", headers=admin_headers
    ).get_json()["data"]
    managers_b = client.get(
        f"/api/v1/locations/{loc_b['id']}/managers", headers=admin_headers
    ).get_json()["data"]
    assert all(m["id"] != manager.id for m in managers_a)
    assert any(m["id"] == manager.id for m in managers_b)
