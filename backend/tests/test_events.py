"""Tests for security event ingestion, batch processing, validations, and filtering."""

from uuid import uuid4

from fastapi.testclient import TestClient


def _register_device(client: TestClient, device_id: str | None = None) -> tuple[str, str]:
    """Helper to register a device and return (device_id, token)."""
    dev_id = device_id or f"dev-{uuid4().hex[:8]}"
    resp = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": dev_id,
            "device_name": f"Device {dev_id}",
            "operating_system": "Windows 11",
            "agent_version": "1.0.0",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    return data["device_id"], data["token"]


def test_single_event_ingestion_success(client: TestClient, admin_token: str) -> None:
    """Device can ingest a single event, and analyst/admin can read it."""
    dev_id, token = _register_device(client)
    evt_id = f"evt-{uuid4().hex[:8]}"

    # Ingest event
    resp = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_id": evt_id,
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "USB_ACTIVITY",
            "action": "USB_WRITE",
            "file_name": "passwords.xlsx",
            "file_path": "D:\\passwords.xlsx",
            "file_size": 1048576,
            "sensitivity_level": "HIGHLY_CONFIDENTIAL",
            "risk_score": 92.5,
            "decision": "BLOCK",
            "metadata_json": {"vendor_id": "0781", "product_id": "5581"},
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_id"] == evt_id
    assert data["decision"] == "BLOCK"
    assert data["risk_score"] == 92.5

    # Get event by ID
    get_resp = client.get(
        f"/api/v1/events/{evt_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["file_name"] == "passwords.xlsx"


def test_event_ingestion_unauthorized_token_fails(client: TestClient) -> None:
    """Event ingestion without or with invalid token must fail with 401."""
    # No auth header
    resp1 = client.post(
        "/api/v1/events",
        json={
            "event_id": f"evt-{uuid4().hex[:8]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
        },
    )
    assert resp1.status_code == 401

    # Invalid token
    resp2 = client.post(
        "/api/v1/events",
        headers={"Authorization": "Bearer invalid-device-token-123"},
        json={
            "event_id": f"evt-{uuid4().hex[:8]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
        },
    )
    assert resp2.status_code == 401


def test_event_ingestion_disabled_device_fails(client: TestClient, admin_token: str) -> None:
    """A disabled device cannot ingest events."""
    dev_id, token = _register_device(client)

    # Disable device as admin
    dis_resp = client.post(
        f"/api/v1/devices/{dev_id}/disable",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dis_resp.status_code == 200

    # Try ingesting event
    resp = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_id": f"evt-{uuid4().hex[:8]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
        },
    )
    assert resp.status_code == 401
    assert "disabled" in resp.json()["error"]["message"].lower()


def test_duplicate_event_id_fails(client: TestClient) -> None:
    """Duplicate event_id should return 409 Conflict."""
    dev_id, token = _register_device(client)
    evt_id = f"evt-dup-{uuid4().hex[:8]}"

    payload = {
        "event_id": evt_id,
        "timestamp": "2026-09-17T12:00:00Z",
        "event_type": "FILE_ACCESS",
    }

    resp1 = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp1.status_code == 201

    # Second submission with exact same event_id
    resp2 = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp2.status_code == 409


def test_batch_event_ingestion_success(client: TestClient) -> None:
    """Device can ingest a batch of security events."""
    dev_id, token = _register_device(client)

    batch_payload = {
        "events": [
            {
                "event_id": f"evt-batch-{uuid4().hex[:8]}",
                "timestamp": "2026-09-17T12:01:00Z",
                "event_type": "FILE_COPY",
                "file_name": f"doc_{i}.docx",
                "sensitivity_level": "INTERNAL",
                "risk_score": 15.0 + i,
            }
            for i in range(5)
        ]
    }

    resp = client.post(
        "/api/v1/events/batch",
        headers={"Authorization": f"Bearer {token}"},
        json=batch_payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["accepted"] == 5
    assert data["rejected"] == 0


def test_batch_event_ingestion_exceeds_max_fails(client: TestClient) -> None:
    """Batch exceeding MAX_BATCH_SIZE (100) should be rejected."""
    dev_id, token = _register_device(client)

    large_batch = {
        "events": [
            {
                "event_id": f"evt-over-{i}-{uuid4().hex[:6]}",
                "timestamp": "2026-09-17T12:00:00Z",
                "event_type": "FILE_ACCESS",
            }
            for i in range(105)
        ]
    }

    resp = client.post(
        "/api/v1/events/batch",
        headers={"Authorization": f"Bearer {token}"},
        json=large_batch,
    )
    assert resp.status_code == 409
    assert "exceeds maximum" in resp.json()["error"]["message"].lower()


def test_event_validation_risk_score_bounds(client: TestClient) -> None:
    """Risk score must be between 0.0 and 100.0."""
    dev_id, token = _register_device(client)

    # Risk score > 100
    resp1 = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_id": f"evt-val-{uuid4().hex[:8]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
            "risk_score": 150.0,
        },
    )
    assert resp1.status_code == 422

    # Risk score < 0
    resp2 = client.post(
        "/api/v1/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "event_id": f"evt-val-{uuid4().hex[:8]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
            "risk_score": -10.0,
        },
    )
    assert resp2.status_code == 422


def test_get_events_filtering_and_pagination(client: TestClient, admin_token: str) -> None:
    """Test filtering events by attributes, decision, and pagination."""
    dev_id, token = _register_device(client)

    # Seed 3 distinct events
    events_data = [
        {
            "event_id": f"filter-1-{uuid4().hex[:6]}",
            "timestamp": "2026-09-17T10:00:00Z",
            "event_type": "USB_ACTIVITY",
            "sensitivity_level": "HIGHLY_CONFIDENTIAL",
            "risk_score": 95.0,
            "decision": "BLOCK",
        },
        {
            "event_id": f"filter-2-{uuid4().hex[:6]}",
            "timestamp": "2026-09-17T11:00:00Z",
            "event_type": "NETWORK_TRANSFER",
            "sensitivity_level": "CONFIDENTIAL",
            "risk_score": 60.0,
            "decision": "ALLOW",
        },
        {
            "event_id": f"filter-3-{uuid4().hex[:6]}",
            "timestamp": "2026-09-17T12:00:00Z",
            "event_type": "FILE_ACCESS",
            "sensitivity_level": "PUBLIC",
            "risk_score": 10.0,
            "decision": "ALLOW",
        },
    ]

    for ev in events_data:
        r = client.post("/api/v1/events", headers={"Authorization": f"Bearer {token}"}, json=ev)
        assert r.status_code == 201

    # Filter by device_id
    r_dev = client.get(
        f"/api/v1/events?device_id={dev_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_dev.status_code == 200
    assert r_dev.json()["total"] >= 3

    # Filter by min_risk_score=90
    r_risk = client.get(
        f"/api/v1/events?device_id={dev_id}&min_risk_score=90",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_risk.status_code == 200
    assert r_risk.json()["total"] == 1
    assert r_risk.json()["items"][0]["risk_score"] == 95.0

    # Filter by decision=BLOCK
    r_dec = client.get(
        f"/api/v1/events?device_id={dev_id}&decision=BLOCK",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_dec.status_code == 200
    assert r_dec.json()["total"] == 1
    assert r_dec.json()["items"][0]["decision"] == "BLOCK"

    # Test pagination
    r_page = client.get(
        f"/api/v1/events?device_id={dev_id}&page=1&size=2",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r_page.status_code == 200
    assert len(r_page.json()["items"]) == 2
    assert r_page.json()["pages"] >= 2
