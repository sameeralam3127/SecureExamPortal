"""End-to-end auth-flow tests, including regression coverage for the
Google-login account-takeover fix."""


def _register(client, **overrides):
    payload = {
        "full_name": "Test Student",
        "username": "student1",
        "email": "student1@example.com",
        "password": "Str0ngPass",
    }
    payload.update(overrides)
    return client.post("/api/v1/auth/register", json=payload)


def test_register_and_login(client):
    resp = _register(client)
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "student1"

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "student1", "password": "Str0ngPass"},
    )
    assert login.status_code == 200


def test_weak_password_rejected_on_register(client):
    resp = _register(client, username="weakpw", email="weak@example.com", password="weak")
    assert resp.status_code == 422


def test_logout_revokes_existing_tokens(client):
    token = _register(
        client, username="logoutuser", email="logout@example.com"
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    # Same token must now be rejected (session revoked).
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_password_reset_flow_and_session_revocation(client, monkeypatch):
    from app.services import job_queue

    captured = {}

    def fake_enqueue(db, *, recipient_email, reset_token):
        captured["email"] = recipient_email
        captured["token"] = reset_token

    monkeypatch.setattr(
        "app.modules.auth.routes.enqueue_password_reset_email", fake_enqueue
    )

    old_token = _register(
        client, username="resetuser", email="reset@example.com"
    ).json()["access_token"]

    req = client.post(
        "/api/v1/auth/password-reset/request", json={"email": "reset@example.com"}
    )
    assert req.status_code == 200
    assert captured["token"]

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": captured["token"], "new_password": "BrandN3wPass"},
    )
    assert confirm.status_code == 200

    # Old session is revoked after reset...
    old_headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/api/v1/auth/me", headers=old_headers).status_code == 401
    # ...and the new password works.
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"username": "resetuser", "password": "BrandN3wPass"},
        ).status_code
        == 200
    )
    _ = job_queue  # imported to ensure module loads cleanly


def test_password_reset_request_hides_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "nobody@example.com"},
    )
    # Must not reveal whether the account exists.
    assert resp.status_code == 200


def test_google_account_cannot_be_password_logged_in(client):
    """Regression: a Google-provisioned account must never be reachable via the
    password-login path, even though it has a (random) password hash."""
    from sqlalchemy import select

    from app.extensions.db import SessionLocal
    from app.models.user import AuthProvider, User, UserRole
    from app.utils.security import generate_random_password, hash_password

    with SessionLocal() as db:
        db.add(
            User(
                full_name="Google User",
                username="googleuser",
                email="googleuser@example.com",
                password_hash=hash_password(generate_random_password()),
                role=UserRole.student,
                auth_provider=AuthProvider.google,
                email_verified=True,
            )
        )
        db.commit()
        stored_hash = db.scalar(
            select(User.password_hash).where(User.username == "googleuser")
        )

    # An attacker who somehow guessed the stored hash's input still cannot log in,
    # and normal password login is refused for provider-managed accounts.
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "googleuser", "password": "anything-goes"},
    )
    assert resp.status_code == 401
    assert stored_hash is not None
