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


def test_alert_lifecycle(client: TestClient, admin_token: str) -> None:
    """Analyst/Admin can create an alert, acknowledge it, and resolve it."""
    # 1. Create alert
    create_resp = client.post(
        "/api/v1/alerts",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "title": "Suspicious USB Mass Exfiltration",
            "message": "Multiple confidential files transferred to unauthorized USB drive",
            "severity": "CRITICAL",
        },
    )
    assert create_resp.status_code == 201
    alert_data = create_resp.json()
    alert_id = alert_data["id"]
    assert alert_data["status"] == "OPEN"
    assert alert_data["severity"] == "CRITICAL"

    # 2. Acknowledge alert
    ack_resp = client.post(
        f"/api/v1/alerts/{alert_id}/acknowledge",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "SOC analyst investigating device logs"},
    )
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    # 3. Resolve alert
    res_resp = client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "False positive verified with IT supervisor"},
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"
