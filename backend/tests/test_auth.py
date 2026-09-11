"""Tests for authentication endpoints."""

from fastapi.testclient import TestClient

from app.config import get_settings


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
