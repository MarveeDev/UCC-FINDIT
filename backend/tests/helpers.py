from werkzeug.security import generate_password_hash

from app.extensions import db
from app.users.models import User


def create_user(email, role, verified=True, password="Password1"):
    user = User(
        first_name="Test",
        last_name="User",
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        email_verified=verified,
    )
    db.session.add(user)
    db.session.commit()
    return user


def auth_header(client, email, password="Password1"):
    resp = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    token = resp.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
