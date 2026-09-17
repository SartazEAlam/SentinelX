"""Tests for approval workflow endpoints."""

from app.models.enums import ApprovalStatus
from app.services.approval_service import create_approval
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_list_approvals(client: TestClient, admin_token: str) -> None:
    """Test listing approvals."""
    response = client.get(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_get_approval_not_found(client: TestClient, admin_token: str) -> None:
    """Non-existent approval ID returns 404."""
    response = client.get(
        "/api/v1/approvals/99999",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_approve_and_conflict_handling(
    client: TestClient, db: Session, admin_token: str
) -> None:
    """Test approving a request and verifying subsequent approve attempts conflict."""
    approval = create_approval(db, event_id=101, requested_by=1, reason="Need USB access")
    approval_id = approval.id

    # 1. Approve
    approve_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "Granted for 2 hours"},
    )
    assert approve_response.status_code == 200
    data = approve_response.json()
    assert data["status"] == ApprovalStatus.APPROVED.value
    assert data["reviewer_comment"] == "Granted for 2 hours"

    # 2. Second approve attempt returns 409 Conflict
    conflict_response = client.post(
        f"/api/v1/approvals/{approval_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"comment": "Attempt duplicate approve"},
    )
    assert conflict_response.status_code == 409
    assert conflict_response.json()["error"]["code"] == "CONFLICT"


def test_reject_approval_as_viewer_fails(client: TestClient, viewer_token: str) -> None:
    """Viewer cannot approve or reject approval requests."""
    response = client.post(
        "/api/v1/approvals/1/reject",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"comment": "Unauthorized reject attempt"},
    )
    assert response.status_code == 403


def test_create_approval_request(client: TestClient, viewer_token: str) -> None:
    """User can submit an approval request."""
    response = client.post(
        "/api/v1/approvals",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"event_id": 202, "reason": "Need temporary access to file"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == 202
    assert data["status"] == "PENDING"
    assert data["reason"] == "Need temporary access to file"
    assert "request_id" in data

