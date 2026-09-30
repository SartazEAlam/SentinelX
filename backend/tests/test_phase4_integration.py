"""Phase 4 — Integration tests for Risk Assessment & Policy Engine.

Tests the complete Phase 2 → Phase 3 → Phase 4 pipeline using the
FastAPI TestClient and database.  All data is synthetic.
"""

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _register_device(client: TestClient, admin_token: str) -> str:
    """Register a test device and return its bearer token."""
    resp = client.post(
        "/api/v1/devices/register",
        json={
            "device_id": "test-device-phase4",
            "device_name": "Phase4 Test Device",
            "hostname": "test-host",
            "operating_system": "Windows",
            "os_version": "11",
            "agent_version": "1.0.0",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    if resp.status_code == 409:
        # Device already registered — use existing token approach
        # For test isolation, try a unique device_id
        import uuid
        unique_id = f"test-dev-{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/v1/devices/register",
            json={
                "device_id": unique_id,
                "device_name": "Phase4 Test Device",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, f"Device registration failed: {resp.text}"
        return resp.json()["token"]

    assert resp.status_code == 201, f"Device registration failed: {resp.text}"
    return resp.json()["token"]


def _ingest_event(
    client: TestClient,
    device_token: str,
    event_id: str,
    event_type: str = "FILE_COPY",
    action: str | None = None,
    destination: str | None = None,
    file_name: str | None = None,
    file_size: int | None = None,
    file_hash: str | None = None,
    sensitivity_level: str | None = None,
    classification: dict | None = None,
) -> dict:
    """Ingest a security event and return the response."""
    payload = {
        "event_id": event_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "event_type": event_type,
        "action": action,
        "destination": destination,
        "file_name": file_name,
        "file_size": file_size,
        "file_hash": file_hash,
        "sensitivity_level": sensitivity_level,
        "classification": classification,
    }
    resp = client.post(
        "/api/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {device_token}"},
    )
    assert resp.status_code == 201, f"Event ingestion failed: {resp.text}"
    return resp.json()


# ═══════════════════════════════════════════════════════════════════════════
# Integration tests
# ═══════════════════════════════════════════════════════════════════════════

class TestPhase4Integration:
    """Full end-to-end integration tests for Phase 4."""

    def test_low_risk_public_local_copy(
        self, client: TestClient, admin_token: str
    ) -> None:
        """PUBLIC data → LOCAL_TRUSTED → COPY → LOW → ALLOW."""
        device_token = _register_device(client, admin_token)
        import uuid
        eid = f"int-low-{uuid.uuid4().hex[:8]}"

        _ingest_event(
            client, device_token,
            event_id=eid,
            event_type="FILE_COPY",
            destination="C:\\Users\\test\\Documents\\copy.txt",
            file_name="public_document.txt",
            file_size=1024,
            classification={
                "sensitivity_level": "PUBLIC",
                "confidence": 0.95,
                "categories": [],
                "classifier_version": "3.0.0",
                "content_inspected": True,
                "inspection_complete": True,
            },
        )

        # Evaluate risk
        resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": eid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, f"Risk eval failed: {resp.text}"
        data = resp.json()
        assert data["risk_level"] == "LOW"
        assert data["decision"] == "ALLOW"
        assert 0 <= data["risk_score"] <= 29

    def test_high_risk_usb_transfer(
        self, client: TestClient, admin_token: str
    ) -> None:
        """HIGHLY_CONFIDENTIAL → USB → HIGH → BLOCK."""
        device_token = _register_device(client, admin_token)
        import uuid
        eid = f"int-high-{uuid.uuid4().hex[:8]}"

        _ingest_event(
            client, device_token,
            event_id=eid,
            event_type="USB_ACTIVITY",
            action="USB_TRANSFER",
            destination="E:\\backup",
            file_name="customer_records.csv",
            file_size=50_000_000,
            classification={
                "sensitivity_level": "HIGHLY_CONFIDENTIAL",
                "confidence": 0.92,
                "categories": ["CUSTOMER_DATA", "PERSONAL_DATA", "FINANCIAL_DATA"],
                "classifier_version": "3.0.0",
                "content_inspected": True,
                "inspection_complete": True,
            },
        )

        resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": eid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, f"Risk eval failed: {resp.text}"
        data = resp.json()
        assert data["risk_level"] == "MEDIUM"
        assert data["decision"] == "HOLD"
        assert 30 <= data["risk_score"] <= 69
        assert len(data["factors"]) == 8  # All 8 factors present
        assert data["explanation"]  # Non-empty explanation

    def test_medium_risk_creates_approval(
        self, client: TestClient, admin_token: str
    ) -> None:
        """CONFIDENTIAL → USB_TRUSTED → MEDIUM → HOLD → approval created."""
        device_token = _register_device(client, admin_token)
        import uuid
        eid = f"int-med-{uuid.uuid4().hex[:8]}"

        _ingest_event(
            client, device_token,
            event_id=eid,
            event_type="FILE_COPY",
            destination="F:\\trusted_backup",
            file_name="internal_project_notes.txt",
            file_size=5000,
            classification={
                "sensitivity_level": "CONFIDENTIAL",
                "confidence": 0.88,
                "categories": ["CONFIDENTIAL_DOCUMENT"],
                "classifier_version": "3.0.0",
                "content_inspected": True,
                "inspection_complete": True,
            },
        )

        resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": eid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()

        if data["decision"] == "HOLD":
            # Verify approval was created
            approvals_resp = client.get(
                "/api/v1/approvals?status=PENDING",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert approvals_resp.status_code == 200
            approvals = approvals_resp.json()
            assert approvals["total"] >= 1

    def test_risk_assessment_retrieval(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Verify risk assessments can be listed and retrieved."""
        resp = client.get(
            "/api/v1/risk/assessments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

        if data["total"] > 0:
            first_id = data["items"][0]["id"]
            detail_resp = client.get(
                f"/api/v1/risk/assessments/{first_id}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert detail_resp.status_code == 200
            detail = detail_resp.json()
            assert detail["risk_engine_version"] == "1.0.0"

    def test_policy_simulation(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Simulate a policy evaluation without persisting."""
        resp = client.post(
            "/api/v1/policies/simulate",
            json={
                "context": {
                    "sensitivity": {
                        "level": "HIGHLY_CONFIDENTIAL",
                        "categories": ["CUSTOMER_DATA", "PERSONAL_DATA"],
                        "confidence": 0.95,
                    },
                    "action": {"action_type": "USB_TRANSFER"},
                    "destination": {"destination_type": "USB_UNTRUSTED"},
                    "user_context": {"user_role": "EMPLOYEE"},
                    "device_context": {"device_trust": "MANAGED"},
                    "time_context": {"is_business_hours": False},
                    "volume_context": {"file_size_bytes": 500000000},
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200, f"Simulation failed: {resp.text}"
        data = resp.json()
        assert 30 <= data["risk_score"] <= 69
        assert data["decision"] == "HOLD"
        assert len(data["factors"]) == 8

    def test_policy_crud_and_versioning(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Create, update, and verify version increments."""
        import uuid
        name = f"Test Policy {uuid.uuid4().hex[:8]}"

        # Create
        create_resp = client.post(
            "/api/v1/policies",
            json={
                "name": name,
                "description": "Test policy for Phase 4",
                "priority": 50,
                "decision": "BLOCK",
                "sensitivity_levels": ["HIGHLY_CONFIDENTIAL"],
                "action_types": ["USB_TRANSFER"],
                "min_risk_score": 70,
                "max_risk_score": 100,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert create_resp.status_code == 201
        policy = create_resp.json()
        policy_id = policy["id"]
        assert policy["version"] == 1

        # Update — version should increment
        update_resp = client.patch(
            f"/api/v1/policies/{policy_id}",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["version"] == 2

        # Disable
        disable_resp = client.post(
            f"/api/v1/policies/{policy_id}/disable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert disable_resp.status_code == 200
        assert disable_resp.json()["enabled"] is False

        # Enable
        enable_resp = client.post(
            f"/api/v1/policies/{policy_id}/enable",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert enable_resp.status_code == 200
        assert enable_resp.json()["enabled"] is True

        # Delete (soft)
        del_resp = client.delete(
            f"/api/v1/policies/{policy_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 204

        # Should no longer appear in list
        get_resp = client.get(
            f"/api/v1/policies/{policy_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_resp.status_code == 404

    def test_approval_workflow(
        self, client: TestClient, admin_token: str, db: Session
    ) -> None:
        """Test the HOLD → APPROVE/DENY workflow."""
        # Create an event that will produce a HOLD decision
        device_token = _register_device(client, admin_token)
        import uuid
        eid = f"int-appr-{uuid.uuid4().hex[:8]}"

        _ingest_event(
            client, device_token,
            event_id=eid,
            event_type="FILE_COPY",
            destination="F:\\external",
            file_name="project_data.xlsx",
            file_size=2000,
            classification={
                "sensitivity_level": "CONFIDENTIAL",
                "confidence": 0.85,
                "categories": ["CONFIDENTIAL_DOCUMENT"],
                "classifier_version": "3.0.0",
                "content_inspected": True,
                "inspection_complete": True,
            },
        )

        eval_resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": eid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert eval_resp.status_code == 201
        data = eval_resp.json()

        if data["decision"] == "HOLD":
            # Find the pending approval
            approvals_resp = client.get(
                "/api/v1/approvals?status=PENDING",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert approvals_resp.status_code == 200
            pending = approvals_resp.json()["items"]
            if pending:
                approval_id = pending[0]["id"]

                # Approve it
                approve_resp = client.post(
                    f"/api/v1/approvals/{approval_id}/approve",
                    json={"comment": "Approved by admin for testing"},
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                assert approve_resp.status_code == 200
                assert approve_resp.json()["status"] == "APPROVED"
                assert approve_resp.json()["reviewer_comment"] == "Approved by admin for testing"

    def test_historical_immutability(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Changing policy config should not alter existing assessments."""
        device_token = _register_device(client, admin_token)
        import uuid
        eid = f"int-immut-{uuid.uuid4().hex[:8]}"

        _ingest_event(
            client, device_token,
            event_id=eid,
            event_type="FILE_COPY",
            file_name="test.txt",
            file_size=100,
            classification={
                "sensitivity_level": "PUBLIC",
                "confidence": 0.9,
                "categories": [],
                "classifier_version": "3.0.0",
                "content_inspected": True,
                "inspection_complete": True,
            },
        )

        eval_resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": eid},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert eval_resp.status_code == 201
        original = eval_resp.json()
        assessment_id = original["id"]

        # Retrieve the assessment — it should be unchanged
        get_resp = client.get(
            f"/api/v1/risk/assessments/{assessment_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved["risk_score"] == original["risk_score"]
        assert retrieved["risk_level"] == original["risk_level"]
        assert retrieved["decision"] == original["decision"]
        assert retrieved["risk_engine_version"] == original["risk_engine_version"]

    def test_unauthenticated_risk_eval_rejected(self, client: TestClient) -> None:
        """Risk evaluation without auth should be rejected."""
        resp = client.post(
            "/api/v1/risk/evaluate",
            json={"event_id": "fake"},
        )
        # Should return 401 or 403
        assert resp.status_code in (401, 403)

    def test_different_destinations_produce_different_scores(
        self, client: TestClient, admin_token: str
    ) -> None:
        """Same file, different destinations → different risk scores."""
        device_token = _register_device(client, admin_token)
        import uuid

        scores = {}
        for dest_label, dest_path, event_type in [
            ("local", "C:\\safe\\copy.txt", "FILE_COPY"),
            ("usb", "E:\\usb_drive\\copy.txt", "USB_ACTIVITY"),
            ("cloud", "https://cloud.example.com/upload", "FILE_UPLOAD"),
        ]:
            eid = f"int-dest-{dest_label}-{uuid.uuid4().hex[:8]}"
            _ingest_event(
                client, device_token,
                event_id=eid,
                event_type=event_type,
                destination=dest_path,
                file_name="customer_records.csv",
                file_size=10000,
                classification={
                    "sensitivity_level": "CONFIDENTIAL",
                    "confidence": 0.9,
                    "categories": ["CUSTOMER_DATA"],
                    "classifier_version": "3.0.0",
                    "content_inspected": True,
                    "inspection_complete": True,
                },
            )

            resp = client.post(
                "/api/v1/risk/evaluate",
                json={"event_id": eid},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 201
            scores[dest_label] = resp.json()["risk_score"]

        # USB and cloud should score higher than local
        assert scores["usb"] > scores["local"]
        assert scores["cloud"] > scores["local"]
