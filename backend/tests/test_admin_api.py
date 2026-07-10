"""Admin management flows: student and exam listing, creation, and deletion."""

import uuid


def _admin_headers(client):
    """Create an admin directly and return an Authorization header for it."""
    from app.extensions.db import SessionLocal
    from app.models.user import AuthProvider, User, UserRole
    from app.utils.security import hash_password

    username = f"admin_{uuid.uuid4().hex[:8]}"
    password = "AdminPass123"
    with SessionLocal() as db:
        db.add(
            User(
                full_name="Portal Admin",
                username=username,
                email=f"{username}@example.com",
                password_hash=hash_password(password),
                role=UserRole.admin,
                auth_provider=AuthProvider.password,
            )
        )
        db.commit()

    token = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _exam_payload(title="Sample Exam"):
    return {
        "title": title,
        "description": "An exam used in tests.",
        "duration_minutes": 15,
        "questions": [
            {
                "question_text": "What is 2 + 2?",
                "option_a": "3",
                "option_b": "4",
                "option_c": "5",
                "option_d": "6",
                "correct_option": "B",
                "marks": 2,
            }
        ],
    }


def test_admin_can_create_list_and_delete_student(client):
    headers = _admin_headers(client)
    suffix = uuid.uuid4().hex[:8]

    created = client.post(
        "/api/v1/admin/students",
        headers=headers,
        json={
            "full_name": "Managed Student",
            "username": f"managed_{suffix}",
            "email": f"managed_{suffix}@example.com",
            "password": "StudentPass1",
        },
    )
    assert created.status_code == 201, created.text
    student_id = created.json()["id"]

    listing = client.get("/api/v1/admin/students", headers=headers)
    assert listing.status_code == 200
    assert any(s["id"] == student_id for s in listing.json())

    deleted = client.delete(f"/api/v1/admin/students/{student_id}", headers=headers)
    assert deleted.status_code == 204

    listing_after = client.get("/api/v1/admin/students", headers=headers).json()
    assert not any(s["id"] == student_id for s in listing_after)


def test_admin_can_create_and_delete_exam(client):
    headers = _admin_headers(client)

    created = client.post(
        "/api/v1/admin/exams", headers=headers, json=_exam_payload("Deletable Exam")
    )
    assert created.status_code == 201, created.text
    exam_id = created.json()["id"]

    assert client.delete(f"/api/v1/admin/exams/{exam_id}", headers=headers).status_code == 204
    assert client.delete(f"/api/v1/admin/exams/{exam_id}", headers=headers).status_code == 404


def test_delete_endpoints_require_admin(client):
    # A student token must not be able to delete anything.
    suffix = uuid.uuid4().hex[:8]
    student_token = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Plain Student",
            "username": f"plain_{suffix}",
            "email": f"plain_{suffix}@example.com",
            "password": "StudentPass1",
        },
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {student_token}"}

    assert client.delete("/api/v1/admin/students/1", headers=headers).status_code == 403
    assert client.delete("/api/v1/admin/exams/1", headers=headers).status_code == 403
