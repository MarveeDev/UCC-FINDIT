from datetime import date, timedelta

from app.claims.models import HandoverCode
from app.extensions import db
from app.users.models import utcnow
from tests.helpers import auth_header, create_user


def _setup_approved(client):
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
            "item_name": "Black Laptop",
            "category": "Electronics",
            "description": "Dell XPS",
            "location_id": loc["id"],
            "location_description": "Near the campus library",
            "event_date": date.today().isoformat(),
        },
        headers=finder_headers,
    ).get_json()["data"]

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

    return {
        "code": approved["collection_code"],
        "claim_id": claim["id"],
        "report_id": report["id"],
        "staff_headers": staff_headers,
        "claimant_headers": claimant_headers,
    }


def test_handover_success_marks_recovered(client):
    ctx = _setup_approved(client)
    resp = client.post(
        "/api/v1/handover/verify",
        json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
        headers=ctx["staff_headers"],
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["status"] == "RECOVERED"

    detail = client.get(
        f"/api/v1/reports/{ctx['report_id']}", headers=ctx["claimant_headers"]
    ).get_json()["data"]
    assert detail["status"] == "RECOVERED"


def test_handover_code_reuse_prevented(client):
    ctx = _setup_approved(client)
    assert (
        client.post(
            "/api/v1/handover/verify",
            json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
            headers=ctx["staff_headers"],
        ).status_code
        == 200
    )
    resp = client.post(
        "/api/v1/handover/verify",
        json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
        headers=ctx["staff_headers"],
    )
    assert resp.status_code == 400


def test_handover_wrong_code_locks_after_attempts(client):
    ctx = _setup_approved(client)
    for _ in range(5):
        resp = client.post(
            "/api/v1/handover/verify",
            json={"claim_id": ctx["claim_id"], "code": "WRONG"},
            headers=ctx["staff_headers"],
        )
        assert resp.status_code == 400
    resp = client.post(
        "/api/v1/handover/verify",
        json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
        headers=ctx["staff_headers"],
    )
    assert resp.status_code == 429


def test_handover_code_expiry(client, app):
    ctx = _setup_approved(client)
    with app.app_context():
        record = HandoverCode.query.filter_by(claim_id=ctx["claim_id"]).first()
        record.expires_at = utcnow() - timedelta(hours=1)
        db.session.commit()

    resp = client.post(
        "/api/v1/handover/verify",
        json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
        headers=ctx["staff_headers"],
    )
    assert resp.status_code == 400


def test_claimant_cannot_verify_handover(client):
    ctx = _setup_approved(client)
    resp = client.post(
        "/api/v1/handover/verify",
        json={"claim_id": ctx["claim_id"], "code": ctx["code"]},
        headers=ctx["claimant_headers"],
    )
    assert resp.status_code == 403


def test_handover_code_stored_hashed(client, app):
    ctx = _setup_approved(client)
    with app.app_context():
        record = HandoverCode.query.filter_by(claim_id=ctx["claim_id"]).first()
        assert record.code_hash != ctx["code"]
        assert len(record.code_hash) > 32
