from datetime import date

from tests.helpers import auth_header, create_user


def _admin(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    return admin, auth_header(client, admin.email)


def _location(client, admin_headers, name="Main Library"):
    return client.post(
        "/api/v1/locations", json={"name": name}, headers=admin_headers
    ).get_json()["data"]


def _manager_for(client, admin_headers, loc, email="manager@ucc.edu.gh"):
    manager = create_user(email, "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )
    return manager, auth_header(client, manager.email)


def _unassigned_report(client, headers, **overrides):
    payload = {
        "report_type": "LOST",
        "item_name": "Black Laptop",
        "category": "Electronics",
        "description": "Dell XPS 13",
        "location_description": "Behind the Science Building",
        "event_date": date.today().isoformat(),
    }
    payload.update(overrides)
    return client.post("/api/v1/reports", json=payload, headers=headers).get_json()["data"]


def _student(client, email="student@stu.ucc.edu.gh"):
    student = create_user(email, "STUDENT")
    return student, auth_header(client, student.email)


def test_super_admin_lists_unassigned_reports(client):
    admin, admin_headers = _admin(client)
    _, student_headers = _student(client)
    _unassigned_report(client, student_headers)

    resp = client.get("/api/v1/admin/unassigned-reports", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total"] == 1
    item = data["items"][0]
    assert item["location_id"] is None
    assert item["location_description"] == "Behind the Science Building"


def test_ordinary_users_cannot_list_admin_queue(client):
    _, student_headers = _student(client)
    assert client.get("/api/v1/admin/unassigned-reports", headers=student_headers).status_code == 403

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    manager_headers = auth_header(client, manager.email)
    assert client.get("/api/v1/admin/unassigned-reports", headers=manager_headers).status_code == 403


def test_manager_cannot_assign_report(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, manager_headers = _manager_for(client, admin_headers, loc)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=manager_headers,
    )
    assert resp.status_code == 403


def test_super_admin_assigns_report(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["location_id"] == loc["id"]
    assert data["location_name"] == "Main Library"
    assert data["location_description"] == "Behind the Science Building"


def test_invalid_location_rejected(client):
    admin, admin_headers = _admin(client)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": 9999},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_inactive_location_rejected(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    client.delete(f"/api/v1/locations/{loc['id']}", headers=admin_headers)

    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_already_assigned_report_rejected(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    assert (
        client.post(
            f"/api/v1/admin/reports/{report['id']}/assign",
            json={"location_id": loc["id"]},
            headers=admin_headers,
        ).status_code
        == 200
    )
    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_location_description_and_coords_preserved(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers, latitude=5.1155, longitude=-1.2909)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )
    data = resp.get_json()["data"]
    assert data["location_description"] == "Behind the Science Building"
    assert data["latitude"] == 5.1155
    assert data["longitude"] == -1.2909


def test_managers_notified_after_assignment(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    manager, manager_headers = _manager_for(client, admin_headers, loc)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )

    unread = client.get("/api/v1/notifications/unread-count", headers=manager_headers)
    assert unread.get_json()["data"]["count"] == 1
    listing = client.get("/api/v1/notifications", headers=manager_headers).get_json()["data"]["items"]
    assert listing[0]["type"] == "REPORT_ASSIGNED"


def test_no_manager_assignment_is_safe(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers, "Unmanaged Lab")
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    resp = client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 200


def test_assignment_audit_recorded(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )

    logs = client.get("/api/v1/audit-logs", headers=admin_headers).get_json()["data"]["items"]
    assignment = [l for l in logs if l["action"] == "REPORT_ASSIGNED"]
    assert len(assignment) == 1
    assert assignment[0]["entity_id"] == report["id"]
    assert assignment[0]["metadata"]["new_location_id"] == loc["id"]


def test_manager_sees_report_after_assignment(client):
    admin, admin_headers = _admin(client)
    loc = _location(client, admin_headers)
    _, manager_headers = _manager_for(client, admin_headers, loc)
    _, student_headers = _student(client)
    report = _unassigned_report(client, student_headers)

    client.post(
        f"/api/v1/admin/reports/{report['id']}/assign",
        json={"location_id": loc["id"]},
        headers=admin_headers,
    )

    dash = client.get("/api/v1/dashboard", headers=manager_headers).get_json()["data"]
    names = [r["item_name"] for r in dash["recent_reports"]]
    assert "Black Laptop" in names


def test_unassigned_pagination_and_search(client):
    admin, admin_headers = _admin(client)
    _, student_headers = _student(client)
    _unassigned_report(client, student_headers, item_name="Black Laptop")
    _unassigned_report(client, student_headers, item_name="Blue Umbrella",
                        location_description="Near the gate")

    resp = client.get("/api/v1/admin/unassigned-reports?per_page=1", headers=admin_headers)
    data = resp.get_json()["data"]
    assert data["total"] == 2
    assert len(data["items"]) == 1

    resp = client.get("/api/v1/admin/unassigned-reports?search=umbrella", headers=admin_headers)
    data = resp.get_json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["item_name"] == "Blue Umbrella"


def test_unassigned_list_has_no_private_fields(client):
    admin, admin_headers = _admin(client)
    _, student_headers = _student(client)
    _unassigned_report(
        client, student_headers,
        identifying_characteristics="SECRET",
    )

    data = client.get("/api/v1/admin/unassigned-reports", headers=admin_headers).get_json()["data"]
    item = data["items"][0]
    assert "identifying_characteristics" not in item
    assert "custody_info" not in item
