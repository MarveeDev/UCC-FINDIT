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


def test_audit_logged_for_staff_assignment(client):
    _, _, _, manager_headers, loc = _manager_and_location(client)
    client.post(
        "/api/v1/staff",
        json={
            "first_name": "Kofi", "last_name": "Asante", "email": "kofi@ucc.edu.gh",
            "password": "Password1", "location_id": loc["id"],
        },
        headers=manager_headers,
    )

    logs = client.get("/api/v1/audit-logs", headers=manager_headers).get_json()["data"]["items"]
    assert any(log["action"] == "STAFF_ASSIGNED" for log in logs)


def test_student_cannot_access_audit(client):
    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)
    assert client.get("/api/v1/audit-logs", headers=headers).status_code == 403


def test_audit_scoped_to_manager_locations(client):
    _, admin_headers, manager, manager_headers, loc = _manager_and_location(client)
    # Second manager for a different location.
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

    # First manager creates staff in their own location (audit entry).
    client.post(
        "/api/v1/staff",
        json={"first_name": "A", "last_name": "B", "email": "staff@ucc.edu.gh",
              "password": "Password1", "location_id": loc["id"]},
        headers=manager_headers,
    )

    # The other manager must not see that audit entry.
    other_logs = client.get(
        "/api/v1/audit-logs", headers=other_manager_headers
    ).get_json()["data"]["items"]
    assert all(log.get("location_id") != loc["id"] for log in other_logs)


def test_audit_logged_for_claim_decision(client):
    from datetime import date

    _, admin_headers, _, manager_headers, loc = _manager_and_location(client)
    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = client.post(
        "/api/v1/reports",
        json={"report_type": "FOUND", "item_name": "Keys", "category": "Keys",
              "description": "A ring of keys", "location_id": loc["id"],
              "location_description": "Near the campus library",
              "event_date": date.today().isoformat()},
        headers=finder_headers,
    ).get_json()["data"]

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "proof"},
        headers=claimant_headers,
    ).get_json()["data"]
    client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED"},
        headers=manager_headers,
    )

    logs = client.get("/api/v1/audit-logs", headers=manager_headers).get_json()["data"]["items"]
    assert any(log["action"] == "CLAIM_DECIDED" for log in logs)
