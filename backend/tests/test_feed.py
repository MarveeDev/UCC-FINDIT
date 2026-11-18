from datetime import date

from tests.helpers import auth_header, create_user


def _setup(client):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    lib = client.post(
        "/api/v1/locations", json={"name": "Main Library"}, headers=admin_headers
    ).get_json()["data"]
    hostel = client.post(
        "/api/v1/locations", json={"name": "Hostel"}, headers=admin_headers
    ).get_json()["data"]

    student = create_user("student@stu.ucc.edu.gh", "STUDENT")
    headers = auth_header(client, student.email)

    today = date.today().isoformat()
    reports = []
    for payload in [
        {"report_type": "LOST", "item_name": "Black Laptop", "category": "Electronics",
         "description": "Dell XPS", "location_id": lib["id"], "location_description": "Near the campus library", "event_date": today},
        {"report_type": "FOUND", "item_name": "Blue Umbrella", "category": "Other",
         "description": "Large golf umbrella", "location_id": hostel["id"], "location_description": "Near the campus library", "event_date": today},
        {"report_type": "FOUND", "item_name": "Water Bottle", "category": "Water Bottles",
         "description": "Steel bottle with stickers", "location_id": lib["id"], "location_description": "Near the campus library", "event_date": today},
    ]:
        r = client.post("/api/v1/reports", json=payload, headers=headers)
        reports.append(r.get_json()["data"])
    return headers, lib, hostel, reports


def test_feed_returns_all_reports(client):
    headers, _, _, reports = _setup(client)
    resp = client.get("/api/v1/feed", headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["total"] == 3
    assert {r["item_name"] for r in data["items"]} == {
        "Black Laptop", "Blue Umbrella", "Water Bottle",
    }


def test_feed_filter_by_type(client):
    headers, _, _, _ = _setup(client)
    found = client.get("/api/v1/feed?type=found", headers=headers).get_json()["data"]
    assert found["total"] == 2
    assert all(i["report_type"] == "FOUND" for i in found["items"])

    lost = client.get("/api/v1/feed?type=lost", headers=headers).get_json()["data"]
    assert lost["total"] == 1


def test_feed_filter_by_search(client):
    headers, _, _, _ = _setup(client)
    data = client.get("/api/v1/feed?search=laptop", headers=headers).get_json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["item_name"] == "Black Laptop"


def test_feed_filter_by_location(client):
    headers, _, hostel, _ = _setup(client)
    data = client.get(
        f"/api/v1/feed?location_id={hostel['id']}", headers=headers
    ).get_json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["item_name"] == "Blue Umbrella"


def test_feed_filter_by_category(client):
    headers, _, _, _ = _setup(client)
    data = client.get(
        "/api/v1/feed?category=Electronics", headers=headers
    ).get_json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["category"] == "Electronics"


def test_feed_pagination(client):
    headers, _, _, _ = _setup(client)
    page = client.get("/api/v1/feed?page=1&per_page=2", headers=headers).get_json()["data"]
    assert page["total"] == 3
    assert page["pages"] == 2
    assert len(page["items"]) == 2
