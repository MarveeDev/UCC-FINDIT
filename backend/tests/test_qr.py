from datetime import date

from tests.helpers import auth_header, create_user


def test_register_qr(client):
    owner = create_user("owner@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, owner.email)
    resp = client.post(
        "/api/v1/qr",
        json={"item_name": "Black Laptop", "description": "Dell XPS 13"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["token"]
    assert data["qr_url"].startswith("/recover/")


def test_qr_lookup_does_not_expose_owner(client):
    owner = create_user("owner@stu.ucc.edu.gh", "STUDENT")
    owner_headers = auth_header(client, owner.email)
    token = client.post(
        "/api/v1/qr", json={"item_name": "Wallet"}, headers=owner_headers
    ).get_json()["data"]["token"]

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    resp = client.get(f"/api/v1/qr/{token}", headers=finder_headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["item_name"] == "Wallet"
    assert "email" not in data
    assert "owner" not in data
    assert "token" not in data


def test_qr_report_found_notifies_owner(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": "Hostel"}, headers=admin_headers
    ).get_json()["data"]

    owner = create_user("owner@stu.ucc.edu.gh", "STUDENT")
    owner_headers = auth_header(client, owner.email)
    token = client.post(
        "/api/v1/qr", json={"item_name": "Black Laptop"}, headers=owner_headers
    ).get_json()["data"]["token"]

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    resp = client.post(
        f"/api/v1/qr/{token}/report-found",
        json={
            "category": "Electronics",
            "description": "Found a laptop near the library",
            "location_id": loc["id"],
            "event_date": date.today().isoformat(),
        },
        headers=finder_headers,
    )
    assert resp.status_code == 201

    notes = client.get("/api/v1/notifications", headers=owner_headers).get_json()["data"]["items"]
    assert any(n["type"] == "QR_ITEM_FOUND" for n in notes)


def test_qr_deactivate(client):
    owner = create_user("owner@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, owner.email)
    qr = client.post(
        "/api/v1/qr", json={"item_name": "Wallet"}, headers=headers
    ).get_json()["data"]

    resp = client.post(f"/api/v1/qr/{qr['id']}/deactivate", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["data"]["is_active"] is False

    finder = create_user("finder@stu.ucc.edu.gh", "STUDENT")
    finder_headers = auth_header(client, finder.email)
    assert client.get(f"/api/v1/qr/{qr['token']}", headers=finder_headers).status_code == 404


def test_qr_deactivate_requires_owner(client):
    owner = create_user("owner@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, owner.email)
    qr = client.post(
        "/api/v1/qr", json={"item_name": "Wallet"}, headers=headers
    ).get_json()["data"]

    other = create_user("other@stu.ucc.edu.gh", "STUDENT")
    other_headers = auth_header(client, other.email)
    assert (
        client.post(f"/api/v1/qr/{qr['id']}/deactivate", headers=other_headers).status_code
        == 403
    )
