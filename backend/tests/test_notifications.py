from datetime import date

from tests.helpers import auth_header, create_user


def test_report_notifies_responsible_manager(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    lib = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{lib['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    client.post(
        "/api/v1/reports",
        json={
            "report_type": "LOST",
            "item_name": "Black Laptop",
            "category": "Electronics",
            "description": "Dell XPS",
            "location_id": lib["id"],
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=student_headers,
    )

    manager_headers = auth_header(client, manager.email)
    unread = client.get("/api/v1/notifications/unread-count", headers=manager_headers)
    assert unread.get_json()["data"]["count"] == 1

    listing = client.get("/api/v1/notifications", headers=manager_headers).get_json()["data"]
    assert listing["items"][0]["type"] == "NEW_REPORT"
    assert listing["items"][0]["is_read"] is False


def test_no_notification_when_location_has_no_manager(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    orphan = client.post(
        "/api/v1/locations", json={"name": "Unmanaged Lab"}, headers=admin_headers
    ).get_json()["data"]

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    resp = client.post(
        "/api/v1/reports",
        json={
            "report_type": "FOUND",
            "item_name": "Keys",
            "category": "Keys",
            "description": "A ring of keys",
            "location_id": orphan["id"],
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=student_headers,
    )
    assert resp.status_code == 201

    student_headers = auth_header(client, student.email)
    count = client.get("/api/v1/notifications/unread-count", headers=student_headers)
    assert count.get_json()["data"]["count"] == 0


def test_mark_notification_read(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    lib = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]

    manager = create_user("manager@ucc.edu.gh", "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{lib['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    client.post(
        "/api/v1/reports",
        json={
            "report_type": "LOST",
            "item_name": "Phone",
            "category": "Electronics",
            "description": "iPhone in a case",
            "location_id": lib["id"],
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=student_headers,
    )

    manager_headers = auth_header(client, manager.email)
    notification_id = client.get(
        "/api/v1/notifications", headers=manager_headers
    ).get_json()["data"]["items"][0]["id"]

    resp = client.patch(
        f"/api/v1/notifications/{notification_id}/read", headers=manager_headers
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_read"] is True

    unread = client.get("/api/v1/notifications/unread-count", headers=manager_headers)
    assert unread.get_json()["data"]["count"] == 0
