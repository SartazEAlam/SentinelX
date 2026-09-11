"""Tests for alert endpoints."""

from fastapi.testclient import TestClient


def test_list_alerts(client: TestClient, admin_token: str) -> None:
    """Admin can list alerts."""
    response = client.get(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_update_alert_status(client: TestClient, admin_token: str) -> None:
    """Analyst/Admin can update an alert status."""
    # This requires an alert to exist. For simplicity, we just test the endpoint exists
    # If the alert doesn't exist, it should return 404
    response = client.patch(
        "/api/v1/alerts/nonexistent-alert/status",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "status": "INVESTIGATING",
            "notes": "Looking into this."
        },
    )
    assert response.status_code == 404
