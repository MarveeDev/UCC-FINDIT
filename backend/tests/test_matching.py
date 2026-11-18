from datetime import date

from tests.helpers import auth_header, create_user


def _admin_and_location(client, name="Main Library"):
    admin = create_user("admin@ucc.edu.gh", "SUPER_ADMIN")
    admin_headers = auth_header(client, admin.email)
    loc = client.post(
        "/api/v1/locations", json={"name": name}, headers=admin_headers
    ).get_json()["data"]
    return admin, admin_headers, loc


def _report(client, headers, location_id, report_type, item_name, category, description, **extra):
    payload = {
        "report_type": report_type,
        "item_name": item_name,
        "category": category,
        "description": description,
        "location_id": location_id,
        "event_date": date.today().isoformat(),
        **extra,
    }
    return client.post("/api/v1/reports", json=payload, headers=headers).get_json()["data"]


def test_matching_creates_match_for_similar_items(client):
    _, admin_headers, loc = _admin_and_location(client)
    lost_user = create_user("lost@stu.ucc.edu.gh", "STUDENT")
    found_user = create_user("found@stu.ucc.edu.gh", "STUDENT")
    lost_headers = auth_header(client, lost_user.email)
    found_headers = auth_header(client, found_user.email)

    found = _report(
        client, found_headers, loc["id"], "FOUND", "Black Dell Laptop",
        "Electronics", "Dell XPS 13 in a black sleeve", brand="Dell", colour="Black",
    )
    lost = _report(
        client, lost_headers, loc["id"], "LOST", "Black Dell Laptop",
        "Electronics", "Lost my Dell XPS 13 laptop", brand="Dell", colour="Black",
    )

    matches = client.get("/api/v1/matches", headers=lost_headers).get_json()["data"]
    assert len(matches) == 1
    match = matches[0]
    assert match["score"] >= 50
    assert match["lost_report"]["id"] == lost["id"]
    assert match["found_report"]["id"] == found["id"]
    assert match["reasons"]


def test_matching_does_not_match_same_type(client):
    _, admin_headers, loc = _admin_and_location(client)
    u1 = create_user("a@stu.ucc.edu.gh", "STUDENT")
    u2 = create_user("b@stu.ucc.edu.gh", "STUDENT")
    h1 = auth_header(client, u1.email)
    h2 = auth_header(client, u2.email)
    _report(client, h1, loc["id"], "LOST", "Blue Umbrella", "Other", "Large blue umbrella")
    _report(client, h2, loc["id"], "LOST", "Blue Umbrella", "Other", "Another blue umbrella")
    assert client.get("/api/v1/matches", headers=h1).get_json()["data"] == []


def test_matching_does_not_match_different_categories(client):
    _, admin_headers, loc = _admin_and_location(client)
    u1 = create_user("a@stu.ucc.edu.gh", "STUDENT")
    u2 = create_user("b@stu.ucc.edu.gh", "STUDENT")
    h1 = auth_header(client, u1.email)
    h2 = auth_header(client, u2.email)
    _report(client, h1, loc["id"], "LOST", "Phone", "Electronics", "A smartphone")
    _report(client, h2, loc["id"], "FOUND", "Book", "Books & Documents", "A novel")
    assert client.get("/api/v1/matches", headers=h1).get_json()["data"] == []


def test_matching_prevents_duplicate_records(client, app):
    _, admin_headers, loc = _admin_and_location(client)
    found_user = create_user("found@stu.ucc.edu.gh", "STUDENT")
    lost_user = create_user("lost@stu.ucc.edu.gh", "STUDENT")
    found_headers = auth_header(client, found_user.email)
    lost_headers = auth_header(client, lost_user.email)

    _report(client, found_headers, loc["id"], "FOUND", "Black Laptop", "Electronics", "Laptop")
    lost = _report(client, lost_headers, loc["id"], "LOST", "Black Laptop", "Electronics", "Laptop")

    found_matches = client.get("/api/v1/matches", headers=found_headers).get_json()["data"]
    assert len(found_matches) == 1

    # Re-evaluating the same report is idempotent: no duplicate pair is created.
    from app.items.services import get_report
    from app.matching.services import evaluate_report

    with app.app_context():
        assert evaluate_report(get_report(lost["id"])) == []

    found_matches = client.get("/api/v1/matches", headers=found_headers).get_json()["data"]
    assert len(found_matches) == 1


def test_match_notification_sent(client):
    _, admin_headers, loc = _admin_and_location(client)
    found_user = create_user("found@stu.ucc.edu.gh", "STUDENT")
    lost_user = create_user("lost@stu.ucc.edu.gh", "STUDENT")
    found_headers = auth_header(client, found_user.email)
    lost_headers = auth_header(client, lost_user.email)

    _report(client, found_headers, loc["id"], "FOUND", "Black Laptop", "Electronics", "Laptop")
    _report(client, lost_headers, loc["id"], "LOST", "Black Laptop", "Electronics", "Laptop")

    for headers in (found_headers, lost_headers):
        notes = client.get("/api/v1/notifications", headers=headers).get_json()["data"]["items"]
        assert any(n["type"] == "POSSIBLE_MATCH" for n in notes)
