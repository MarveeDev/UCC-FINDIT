DEFAULT_EMAIL = "student@stu.ucc.edu.gh"


def register(client, email=DEFAULT_EMAIL, password="Password1", **overrides):
    payload = {
        "first_name": "Ama",
        "last_name": "Mensah",
        "email": email,
        "password": password,
        **overrides,
    }
    return client.post("/api/v1/auth/register", json=payload)


def test_register_creates_account(client):
    resp = register(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == DEFAULT_EMAIL
    assert body["data"]["role"] == "STUDENT"
    assert "email_verified" not in body["data"]
    assert "dev_otp" not in body


def test_register_rejects_duplicate_email(client):
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_register_validates_input(client):
    resp = register(client, email="not-an-email", password="short")
    assert resp.status_code == 422
    errors = resp.get_json()["errors"]
    assert "email" in errors
    assert "password" in errors


def test_login_success_returns_token(client):
    register(client)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": DEFAULT_EMAIL, "password": "Password1"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["data"]["access_token"]
    assert body["data"]["user"]["email"] == DEFAULT_EMAIL


def test_login_wrong_password(client):
    register(client)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": DEFAULT_EMAIL, "password": "wrong"},
    )
    assert resp.status_code == 401


def _auth_header(client):
    token = client.post(
        "/api/v1/auth/login",
        json={"email": DEFAULT_EMAIL, "password": "Password1"},
    ).get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_me_requires_auth(client):
    assert client.get("/api/v1/users/me").status_code == 401


def test_me_returns_current_user(client):
    register(client)
    resp = client.get("/api/v1/users/me", headers=_auth_header(client))
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == DEFAULT_EMAIL
