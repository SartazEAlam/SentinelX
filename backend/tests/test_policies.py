"""Tests for policy management endpoints."""

from fastapi.testclient import TestClient


def test_list_policies(client: TestClient, admin_token: str) -> None:
    """Admin can list policies."""
    response = client.get(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_create_policy(client: TestClient, admin_token: str) -> None:
    """Admin can create a policy."""
    response = client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Block USB Storage",
            "description": "Block all external USB mass storage devices.",
            "decision": "BLOCK",
            "enabled": True,
            "conditions": {"device_type": "mass_storage"}
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Block USB Storage"
    assert data["decision"] == "BLOCK"


def test_create_policy_as_viewer_fails(client: TestClient, viewer_token: str) -> None:
    """Viewer cannot create a policy."""
    response = client.post(
        "/api/v1/policies",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={
            "name": "Hacker Policy",
            "description": "Should fail",
            "decision": "ALLOW",
            "enabled": True,
            "conditions": {}
        },
    )
    assert response.status_code == 403
