from tests.helpers import auth_header, create_user


def test_super_admin_overview_counts(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)

    create_user("student@stu.ucc.edu.gh", "STUDENT")
    create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    create_user("staff@ucc.edu.gh", "LOCATION_STAFF")
    client.post("/api/v1/locations", json={"name": "Theatre"}, headers=admin_headers)

    resp = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total_students"] == 1
    assert data["total_administrators"] == 1
    assert data["total_staff"] == 1
    assert data["total_theatres"] == 1


def test_overview_requires_super_admin(client):
    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    headers = auth_header(client, manager.email)
    assert client.get("/api/v1/admin/overview", headers=headers).status_code == 403


def test_list_administrators_shows_assignment(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Theatre"}, headers=admin_headers
    ).get_json()["data"]

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )

    resp = client.get("/api/v1/admin/administrators", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()["data"]
    assert any(r["user"]["id"] == manager.id and r["location_id"] == loc["id"] for r in rows)


def test_list_theatres_includes_counts(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    client.post("/api/v1/locations", json={"name": "Theatre"}, headers=admin_headers)

    resp = client.get("/api/v1/admin/theatres", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()["data"]
    assert any(r["name"] == "Theatre" and r["administrator_count"] == 0 for r in rows)
