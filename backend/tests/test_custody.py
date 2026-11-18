from datetime import date

from tests.helpers import auth_header, create_user


def _setup(client):
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

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = client.post(
        "/api/v1/reports",
        json={
            "report_type": "FOUND",
            "item_name": "Wallet",
            "category": "Other",
            "description": "A brown leather wallet",
            "location_id": loc["id"],
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=finder_headers,
    ).get_json()["data"]

    return admin_headers, manager_headers, staff_headers, loc, report, staff


def test_staff_records_custody_received(client):
    _, _, staff_headers, loc, report, staff = _setup(client)
    resp = client.post(
        "/api/v1/custody",
        json={
            "found_report_id": report["id"],
            "event_type": "RECEIVED",
            "staff_id": staff.id,
            "location_id": loc["id"],
        },
        headers=staff_headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["event_type"] == "RECEIVED"


def test_custody_requires_location_access(client):
    _, _, _, loc, report, staff = _setup(client)
    outsider = create_user("outsider@ucc.edu.gh", "LOCATION_STAFF")
    outsider_headers = auth_header(client, outsider.email)
    resp = client.post(
        "/api/v1/custody",
        json={
            "found_report_id": report["id"],
            "event_type": "RECEIVED",
            "staff_id": staff.id,
            "location_id": loc["id"],
        },
        headers=outsider_headers,
    )
    assert resp.status_code == 403


def test_custody_history_and_transfer(client):
    _, _, staff_headers, loc, report, staff = _setup(client)
    client.post(
        "/api/v1/custody",
        json={"found_report_id": report["id"], "event_type": "RECEIVED",
              "staff_id": staff.id, "location_id": loc["id"]},
        headers=staff_headers,
    )
    client.post(
        "/api/v1/custody",
        json={"found_report_id": report["id"], "event_type": "TRANSFERRED",
              "staff_id": staff.id, "location_id": loc["id"], "note": "moved to secure room"},
        headers=staff_headers,
    )

    history = client.get(
        f"/api/v1/custody/{report['id']}", headers=staff_headers
    ).get_json()["data"]
    assert [r["event_type"] for r in history] == ["RECEIVED", "TRANSFERRED"]


def test_custody_rejects_unauthorized_holder(client):
    _, _, staff_headers, loc, report, _ = _setup(client)
    outsider = create_user("outsider@ucc.edu.gh", "LOCATION_STAFF")
    resp = client.post(
        "/api/v1/custody",
        json={
            "found_report_id": report["id"],
            "event_type": "RECEIVED",
            "staff_id": outsider.id,
            "location_id": loc["id"],
        },
        headers=staff_headers,
    )
    assert resp.status_code == 422


def test_custody_rejected_for_recovered_item(client):
    _, manager_headers, staff_headers, loc, report, staff = _setup(client)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "proof"},
        headers=claimant_headers,
    ).get_json()["data"]
    approved = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED"},
        headers=manager_headers,
    ).get_json()["data"]
    client.post(
        "/api/v1/handover/verify",
        json={"claim_id": claim["id"], "code": approved["collection_code"]},
        headers=staff_headers,
    )

    resp = client.post(
        "/api/v1/custody",
        json={
            "found_report_id": report["id"],
            "event_type": "TRANSFERRED",
            "staff_id": staff.id,
            "location_id": loc["id"],
        },
        headers=staff_headers,
    )
    assert resp.status_code == 400


def test_handover_creates_released_custody(client):
    _, manager_headers, staff_headers, loc, report, staff = _setup(client)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "it's mine"},
        headers=claimant_headers,
    ).get_json()["data"]
    approved = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED"},
        headers=manager_headers,
    ).get_json()["data"]

    client.post(
        "/api/v1/handover/verify",
        json={"claim_id": claim["id"], "code": approved["collection_code"]},
        headers=staff_headers,
    )

    history = client.get(
        f"/api/v1/custody/{report['id']}", headers=staff_headers
    ).get_json()["data"]
    assert any(r["event_type"] == "RELEASED" for r in history)
