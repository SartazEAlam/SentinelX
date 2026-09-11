"""Tests for device management and ingestion endpoints."""

from fastapi.testclient import TestClient


def test_device_registration_and_heartbeat(client: TestClient) -> None:
    """Test registering a device and then sending a heartbeat."""

    # 1. Register device
    reg_response = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "hw-id-12345",
            "device_name": "Test Laptop",
            "operating_system": "Windows 11",
            "agent_version": "1.0.0"
        },
    )
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert data["device_id"] == "hw-id-12345"
    assert "token" in data

    device_token = data["token"]

    # 2. Send heartbeat
    hb_response = client.post(
        "/api/v1/devices/heartbeat",
        headers={"Authorization": f"Bearer {device_token}"},
        json={
            "agent_version": "1.0.1",
            "ip_address": "192.168.1.100"
        },
    )
    assert hb_response.status_code == 200
    hb_data = hb_response.json()
    assert hb_data["device_id"] == "hw-id-12345"
    assert hb_data["agent_version"] == "1.0.1"


def test_device_ingest_event(client: TestClient) -> None:
    """Test device ingesting a security event."""

    # Register device
    reg_response = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "hw-id-event-test",
            "device_name": "Event Test Machine"
        },
    )
    device_token = reg_response.json()["token"]

    # Ingest event
    event_response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {device_token}"},
        json={
            "event_id": "evt-123",
            "timestamp": "2026-09-10T12:00:00Z",
            "event_type": "FILE_ACCESS",
            "file_name": "secret.pdf",
            "sensitivity_level": "CONFIDENTIAL",
            "risk_score": 85.0
        },
    )
    if event_response.status_code != 201:
        print(event_response.json())
    assert event_response.status_code == 201
    evt_data = event_response.json()
    assert evt_data["event_id"] == "evt-123"
    assert evt_data["file_name"] == "secret.pdf"


def test_list_devices_as_analyst(client: TestClient, admin_token: str) -> None:
    """Analyst/Admin can list registered devices."""
    # Ensure there is at least one device
    client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "hw-list-test",
            "device_name": "List Test Machine"
        },
    )

    response = client.get(
        "/api/v1/devices",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
