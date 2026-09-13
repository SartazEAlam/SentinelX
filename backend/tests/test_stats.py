"""Tests for the dashboard statistics endpoint."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient


def test_get_overview_stats_empty(client: TestClient, admin_token: str) -> None:
    """Test overview stats with empty database returns expected structure."""
    response = client.get(
        "/api/v1/stats/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_devices" in data
    assert "active_devices" in data
    assert "total_events_24h" in data
    assert "critical_alerts" in data
    assert "pending_approvals" in data
    assert "events_trend" in data
    assert len(data["events_trend"]) == 24
    assert "top_violators" in data


def test_get_overview_stats_as_viewer_succeeds(client: TestClient, viewer_token: str) -> None:
    """Viewer can access dashboard overview statistics."""
    response = client.get(
        "/api/v1/stats/overview",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert response.status_code == 200


def test_get_overview_stats_with_events_buckets_correctly(
    client: TestClient, admin_token: str
) -> None:
    """Ingested security events are correctly reflected in total_events_24h and events_trend."""
    # 1. Register a device
    reg_response = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "hw-stats-dev-1",
            "device_name": "Stats Test Laptop",
            "operating_system": "Windows 11",
        },
    )
    assert reg_response.status_code == 201
    device_token = reg_response.json()["token"]

    # 2. Ingest an event with current timestamp
    now_iso = datetime.now(UTC).isoformat()
    event_response = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {device_token}"},
        json={
            "event_id": "evt-stats-test-1",
            "timestamp": now_iso,
            "event_type": "FILE_ACCESS",
            "file_path": "C:/Confidential/Report.pdf",
            "process_name": "acrobat.exe",
        },
    )
    assert event_response.status_code == 201

    # 3. Query stats overview
    response = client.get(
        "/api/v1/stats/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_devices"] >= 1
    assert data["total_events_24h"] >= 1

    # Verify event trend has at least one bucket with non-zero count
    non_zero_buckets = [b for b in data["events_trend"] if b["count"] > 0]
    assert len(non_zero_buckets) >= 1

    # Verify top violators includes our device
    violator_ids = [v["device_id"] for v in data["top_violators"]]
    assert "hw-stats-dev-1" in violator_ids
