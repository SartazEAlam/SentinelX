"""Approval workflow service."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.approval import ApprovalRequest
from app.models.enums import ApprovalStatus, AuditAction
from app.schemas.approvals import ApprovalActionRequest
from app.services.audit_service import log_action


def get_approval(db: Session, approval_id: int) -> ApprovalRequest:
    """Get an approval request by ID."""
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise NotFoundError("Approval request not found")
    return approval


def list_approvals(
    db: Session, skip: int = 0, limit: int = 50, status: ApprovalStatus | None = None
) -> tuple[list[ApprovalRequest], int]:
    """List approval requests with optional status filtering."""
    query = db.query(ApprovalRequest)
    if status:
        query = query.filter(ApprovalRequest.status == status)

    total = query.count()
    approvals = query.order_by(desc(ApprovalRequest.created_at)).offset(skip).limit(limit).all()
    return approvals, total


def create_approval(
    db: Session, event_id: int, requested_by: int, reason: str | None = None
) -> ApprovalRequest:
    """Create a new approval request for an event."""
    
    # Check if a pending request already exists for this event
    existing = (
        db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.event_id == event_id,
            ApprovalRequest.status == ApprovalStatus.PENDING,
        )
        .first()
    )
    if existing:
        raise ConflictError("A pending approval request already exists for this event")

    approval = ApprovalRequest(
        request_id=str(uuid4()),
        event_id=event_id,
        requested_by=requested_by,
        status=ApprovalStatus.PENDING,
        reason=reason,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    log_action(
        db,
        action=AuditAction.APPROVAL_CREATED,
        actor_user_id=requested_by,
        resource_type="ApprovalRequest",
        resource_id=approval.request_id,
    )
    return approval


def approve_request(
    db: Session, approval_id: int, reviewer_id: int, action_in: ApprovalActionRequest
) -> ApprovalRequest:
    """Approve a pending request."""
    approval = get_approval(db, approval_id)
    if approval.status != ApprovalStatus.PENDING:
        raise ConflictError(f"Cannot approve request with status {approval.status}")

    approval.status = ApprovalStatus.APPROVED
    approval.assigned_to = reviewer_id
    approval.reviewed_at = datetime.now(UTC)
    if action_in.comment:
        approval.reviewer_comment = action_in.comment

    db.commit()
    db.refresh(approval)

    log_action(
        db,
        action=AuditAction.APPROVAL_APPROVED,
        actor_user_id=reviewer_id,
        resource_type="ApprovalRequest",
        resource_id=approval.request_id,
    )
    return approval


def reject_request(
    db: Session, approval_id: int, reviewer_id: int, action_in: ApprovalActionRequest
) -> ApprovalRequest:
    """Reject a pending request."""
    approval = get_approval(db, approval_id)
    if approval.status != ApprovalStatus.PENDING:
        raise ConflictError(f"Cannot reject request with status {approval.status}")

    approval.status = ApprovalStatus.REJECTED
    approval.assigned_to = reviewer_id
    approval.reviewed_at = datetime.now(UTC)
    if action_in.comment:
        approval.reviewer_comment = action_in.comment

    db.commit()
    db.refresh(approval)

    log_action(
        db,
        action=AuditAction.APPROVAL_REJECTED,
        actor_user_id=reviewer_id,
        resource_type="ApprovalRequest",
        resource_id=approval.request_id,
    )
    return approval
