from datetime import date

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
    return admin, admin_headers, manager, auth_header(client, manager.email), loc


def _report(client, headers, location_id, report_type, item_name, category):
    return client.post(
        "/api/v1/reports",
        json={
            "report_type": report_type, "item_name": item_name, "category": category,
            "description": "desc", "location_id": location_id,
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=headers,
    ).get_json()["data"]


def test_dashboard_metrics_scoped(client):
    _, admin_headers, manager, manager_headers, loc = _manager_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)

    _report(client, student_headers, loc["id"], "LOST", "Phone", "Electronics")
    _report(client, student_headers, loc["id"], "FOUND", "Keys", "Keys")

    data = client.get("/api/v1/dashboard", headers=manager_headers).get_json()["data"]
    assert data["metrics"]["lost"] == 1
    assert data["metrics"]["found"] == 1
    assert data["metrics"]["recovered"] == 0


def test_dashboard_manager_isolation(client):
    _, admin_headers, manager, manager_headers, loc = _manager_and_location(client)
    other_loc = client.post(
        "/api/v1/locations", json={"name": "Other Lab"}, headers=admin_headers
    ).get_json()["data"]

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    _report(client, student_headers, other_loc["id"], "LOST", "Book", "Books & Documents")

    data = client.get("/api/v1/dashboard", headers=manager_headers).get_json()["data"]
    assert data["metrics"]["lost"] == 0


def test_super_admin_sees_all(client):
    _, admin_headers, manager, manager_headers, loc = _manager_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)
    _report(client, student_headers, loc["id"], "FOUND", "Keys", "Keys")

    data = client.get("/api/v1/dashboard", headers=admin_headers).get_json()["data"]
    assert data["metrics"]["found"] == 1


def test_student_cannot_access_dashboard(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    assert client.get("/api/v1/dashboard", headers=headers).status_code == 403


def test_analytics_handles_empty(client):
    _, _, manager, manager_headers, loc = _manager_and_location(client)
    data = client.get("/api/v1/analytics", headers=manager_headers).get_json()["data"]
    assert data["lost"] == 0
    assert data["found"] == 0
    assert data["recovery_rate"] == 0.0
    assert data["avg_recovery_days"] is None


def test_analytics_counts_and_categories(client):
    _, _, manager, manager_headers, loc = _manager_and_location(client)
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    student_headers = auth_header(client, student.email)

    _report(client, student_headers, loc["id"], "LOST", "Phone", "Electronics")
    _report(client, student_headers, loc["id"], "FOUND", "Keys", "Keys")

    data = client.get("/api/v1/analytics", headers=manager_headers).get_json()["data"]
    assert data["lost"] == 1
    assert data["found"] == 1
    categories = {c["category"] for c in data["by_category"]}
    assert "Electronics" in categories
    assert "Keys" in categories
