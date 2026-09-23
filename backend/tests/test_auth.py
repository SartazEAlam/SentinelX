"""Tests for authentication endpoints."""

from app.config import get_settings
from fastapi.testclient import TestClient


def test_login_success(client: TestClient) -> None:
    """Test successful login with admin credentials."""
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.FIRST_ADMIN_USERNAME,
            "password": settings.FIRST_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client: TestClient) -> None:
    """Test login with incorrect credentials."""
    settings = get_settings()
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.FIRST_ADMIN_USERNAME,
            "password": "wrong_password",
        },
    )
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_get_me(client: TestClient, admin_token: str) -> None:
    """Test retrieving current user info."""
    settings = get_settings()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == settings.FIRST_ADMIN_USERNAME
    assert data["role"] == "ADMIN"


def test_change_password(client: TestClient, admin_token: str) -> None:
    """Test authenticated user successfully changes password, then fails with wrong password."""
    # Create a user to test password change
    client.post(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "pwd_user",
            "email": "pwd@test.com",
            "password": "OldPassword123!",
            "role": "VIEWER",
        },
    )

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "pwd_user", "password": "OldPassword123!"},
    )
    user_token = login_resp.json()["access_token"]

    # Wrong current password fails
    fail_resp = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"current_password": "WrongPassword!", "new_password": "NewPassword123!"},
    )
    assert fail_resp.status_code == 401

    # Correct current password succeeds
    ok_resp = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"current_password": "OldPassword123!", "new_password": "NewPassword123!"},
    )
    assert ok_resp.status_code == 204

    # Can now login with new password
    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "pwd_user", "password": "NewPassword123!"},
    )
    assert new_login.status_code == 200
