"""Tests for user management endpoints."""

from fastapi.testclient import TestClient


def test_list_users_as_admin(client: TestClient, admin_token: str) -> None:
    """Admin can list users."""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_list_users_as_viewer_fails(client: TestClient, viewer_token: str) -> None:
    """Viewer cannot list users."""
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 403


def test_create_user(client: TestClient, admin_token: str) -> None:
    """Admin can create a new user."""
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "new_analyst",
            "email": "analyst@test.com",
            "password": "StrongPassword123!",
            "full_name": "New Analyst",
            "role": "SECURITY_ANALYST",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_analyst"
    assert data["role"] == "SECURITY_ANALYST"
    assert "id" in data


def test_create_duplicate_user(client: TestClient, admin_token: str) -> None:
    """Cannot create a user with a duplicate username."""
    # Run creation once (it might already exist from previous test if using same DB
    # without rollback)
    client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "dup_user",
            "email": "dup@test.com",
            "password": "StrongPassword123!",
            "role": "VIEWER",
        },
    )

    # Try again
    response = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "dup_user",
            "email": "dup2@test.com",
            "password": "StrongPassword123!",
            "role": "VIEWER",
        },
    )
    assert response.status_code == 409


def test_deactivate_user(client: TestClient, admin_token: str) -> None:
    """Admin can deactivate (soft delete) a user."""
    # Create user
    create_resp = client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "user_to_deactivate",
            "email": "deact@test.com",
            "password": "Password123!",
            "role": "VIEWER",
        },
    )
    user_id = create_resp.json()["id"]

    # Deactivate user
    del_resp = client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["is_active"] is False

    # Inactive user cannot log in
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "user_to_deactivate", "password": "Password123!"},
    )
    assert login_resp.status_code == 401
    assert "inactive" in login_resp.json()["error"]["message"].lower()
