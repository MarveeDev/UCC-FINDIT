from datetime import date

from tests.helpers import auth_header, create_user


def _admin_and_location(client, name="Main Library"):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": name}, headers=admin_headers
    ).get_json()["data"]
    return admin, admin_headers, loc


def _found_report(client, headers, location_id, reporter):
    return client.post(
        "/api/v1/reports",
        json={
            "report_type": "FOUND",
            "item_name": "Black Laptop",
            "category": "Electronics",
            "description": "Dell XPS in a sleeve",
            "location_id": location_id,
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=headers,
    ).get_json()["data"]


def _manager_for_location(client, admin_headers, loc, email="manager@ucc.edu.gh"):
    manager = create_user(email, "LOCATION_MANAGER")
    client.post(
        f"/api/v1/locations/{loc['id']}/managers",
        json={"user_id": manager.id},
        headers=admin_headers,
    )
    return manager, auth_header(client, manager.email)


def test_submit_claim_sets_report_to_claim_pending(client):
    _, admin_headers, loc = _admin_and_location(client)
    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    resp = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "It has a scratch on the lid"},
        headers=claimant_headers,
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["status"] == "PENDING"

    detail = client.get(f"/api/v1/reports/{report['id']}", headers=claimant_headers).get_json()["data"]
    assert detail["status"] == "CLAIM_PENDING"


def test_cannot_claim_own_report(client):
    _, admin_headers, loc = _admin_and_location(client)
    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    resp = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "mine"},
        headers=finder_headers,
    )
    assert resp.status_code == 400


def test_evidence_is_private(client):
    _, admin_headers, loc = _admin_and_location(client)
    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "SECRET-EVIDENCE-123"},
        headers=claimant_headers,
    ).get_json()["data"]

    # A third party cannot see the evidence.
    third_party = create_user("third@stu.ucc.edu.gh", "STUDENT")
    third_headers = auth_header(client, third_party.email)
    resp = client.get(f"/api/v1/claims/{claim['id']}", headers=third_headers)
    assert resp.status_code == 403

    # The claimant sees their own evidence.
    own = client.get(f"/api/v1/claims/{claim['id']}", headers=claimant_headers).get_json()["data"]
    assert own["evidence"] == "SECRET-EVIDENCE-123"


def test_manager_approves_claim_and_generates_code(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager, manager_headers = _manager_for_location(client, admin_headers, loc)

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "proof"},
        headers=claimant_headers,
    ).get_json()["data"]

    resp = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED", "note": "Evidence verified"},
        headers=manager_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["status"] == "APPROVED"
    assert data["collection_code"]
    assert data["report"]["status"] == "APPROVED_FOR_COLLECTION"


def test_student_cannot_review_claim(client):
    _, admin_headers, loc = _admin_and_location(client)
    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "proof"},
        headers=claimant_headers,
    ).get_json()["data"]

    resp = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED"},
        headers=claimant_headers,
    )
    assert resp.status_code == 403


def test_manager_rejects_claim_reopens_report(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager, manager_headers = _manager_for_location(client, admin_headers, loc)

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "weak"},
        headers=claimant_headers,
    ).get_json()["data"]

    resp = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "REJECTED", "note": "Insufficient evidence"},
        headers=manager_headers,
    )
    assert resp.get_json()["data"]["status"] == "REJECTED"

    detail = client.get(f"/api/v1/reports/{report['id']}", headers=claimant_headers).get_json()["data"]
    assert detail["status"] == "OPEN"


def test_claimant_resubmits_after_more_information(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager, manager_headers = _manager_for_location(client, admin_headers, loc)

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claimant = create_user("claimant@stu.ucc.edu.gh", "STUDENT")
    claimant_headers = auth_header(client, claimant.email)
    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "initial"},
        headers=claimant_headers,
    ).get_json()["data"]

    client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "MORE_INFORMATION_REQUIRED"},
        headers=manager_headers,
    )

    resp = client.post(
        f"/api/v1/claims/{claim['id']}/resubmit",
        json={"evidence": "updated evidence"},
        headers=claimant_headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "PENDING"


def test_only_one_claim_can_be_approved(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager, manager_headers = _manager_for_location(client, admin_headers, loc)

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    c1 = create_user("c1@stu.ucc.edu.gh", "STUDENT")
    c2 = create_user("c2@stu.ucc.edu.gh", "STUDENT")
    h1 = auth_header(client, c1.email)
    h2 = auth_header(client, c2.email)
    claim1 = client.post(
        "/api/v1/claims", json={"report_id": report["id"], "evidence": "proof1"}, headers=h1
    ).get_json()["data"]
    claim2 = client.post(
        "/api/v1/claims", json={"report_id": report["id"], "evidence": "proof2"}, headers=h2
    ).get_json()["data"]

    assert (
        client.post(
            f"/api/v1/claims/{claim1['id']}/review",
            json={"decision": "APPROVED"},
            headers=manager_headers,
        ).status_code
        == 200
    )

    # The competing claim is auto-rejected.
    claim2_detail = client.get(
        f"/api/v1/claims/{claim2['id']}", headers=h2
    ).get_json()["data"]
    assert claim2_detail["status"] == "REJECTED"

    # A brand-new claim after approval cannot be approved (409 backstop).
    c3 = create_user("c3@stu.ucc.edu.gh", "STUDENT")
    h3 = auth_header(client, c3.email)
    claim3 = client.post(
        "/api/v1/claims", json={"report_id": report["id"], "evidence": "proof3"}, headers=h3
    ).get_json()["data"]
    resp = client.post(
        f"/api/v1/claims/{claim3['id']}/review",
        json={"decision": "APPROVED"},
        headers=manager_headers,
    )
    assert resp.status_code == 409


def test_manager_cannot_review_own_claim(client):
    _, admin_headers, loc = _admin_and_location(client)
    manager, manager_headers = _manager_for_location(client, admin_headers, loc)

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    report = _found_report(client, finder_headers, loc["id"], finder)

    claim = client.post(
        "/api/v1/claims",
        json={"report_id": report["id"], "evidence": "it's mine"},
        headers=manager_headers,
    ).get_json()["data"]

    resp = client.post(
        f"/api/v1/claims/{claim['id']}/review",
        json={"decision": "APPROVED"},
        headers=manager_headers,
    )
    assert resp.status_code == 403
