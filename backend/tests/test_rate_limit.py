def test_login_rate_limited(client):
    payload = {"email": "nobody@example.com", "password": "wrong-password"}
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json=payload)
        assert resp.status_code == 401
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 429


def test_register_rate_limited(client):
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
