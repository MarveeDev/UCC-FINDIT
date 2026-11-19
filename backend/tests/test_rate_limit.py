from app.security.services import client_ip


def test_client_ip_returns_remote_addr(client):
    with client.application.test_request_context(
        "/", environ_base={"REMOTE_ADDR": "198.51.100.9"}
    ):
        assert client_ip() == "198.51.100.9"


def test_login_rate_limited(client):
    client.application.config["LOGIN_RATE_LIMIT"] = 5
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 429


def test_register_rate_limited(client):
    client.application.config["REGISTER_RATE_LIMIT"] = 3
    payload = {
        "first_name": "Ama",
        "last_name": "Mensah",
        "email": "ama@stu.ucc.edu.gh",
        "password": "Password1",
    }
    for _ in range(3):
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code in (201, 409)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 429


def test_validation_failure_does_not_create_rate_limit_event(client):
    client.application.config["LOGIN_RATE_LIMIT"] = 1
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    # A valid (but wrong-password) attempt is not blocked by the malformed ones.
    resp = client.post(
        "/api/v1/auth/login", json={"email": "x@y.com", "password": "wrong"}
    )
    assert resp.status_code == 401


def test_proxy_fix_honors_forwarded_for(client):
    client.application.config["REGISTER_RATE_LIMIT"] = 1
    payload = {
        "first_name": "Ama",
        "last_name": "Mensah",
        "email": "a@stu.ucc.edu.gh",
        "password": "Password1",
    }
    r1 = client.post(
        "/api/v1/auth/register",
        json=payload,
        headers={"X-Forwarded-For": "203.0.113.7"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "b@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "203.0.113.7"},
    )
    assert r2.status_code == 429


def test_rate_limit_is_per_client_ip(client):
    client.application.config["REGISTER_RATE_LIMIT"] = 1
    payload = {
        "first_name": "Ama",
        "last_name": "Mensah",
        "password": "Password1",
    }

    r1 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "a@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "1.1.1.1"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "b@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "2.2.2.2"},
    )
    assert r2.status_code == 201

    r3 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "c@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "1.1.1.1"},
    )
    assert r3.status_code == 429


def test_proxy_fix_uses_rightmost_forwarded_for(client):
    client.application.config["REGISTER_RATE_LIMIT"] = 1
    payload = {
        "first_name": "Ama",
        "last_name": "Mensah",
        "password": "Password1",
    }

    # A spoofed leftmost entry is ignored; the trusted proxy's rightmost entry wins.
    r1 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "a@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "198.51.100.1, 203.0.113.7"},
    )
    assert r1.status_code == 201

    # The real (rightmost) IP is now rate-limited.
    r2 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "b@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "203.0.113.7"},
    )
    assert r2.status_code == 429

    # The spoofed (leftmost) IP was never recorded and is unaffected.
    r3 = client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "c@stu.ucc.edu.gh"},
        headers={"X-Forwarded-For": "198.51.100.1"},
    )
    assert r3.status_code == 201
