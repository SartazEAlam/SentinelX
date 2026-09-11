"""Approval workflow routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_analyst_or_above, require_viewer_or_above
from app.db.database import get_db
from app.models.approval import ApprovalRequest
from app.models.enums import ApprovalStatus
from app.models.user import User
from app.schemas.approvals import ApprovalActionRequest, ApprovalResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services import approval_service

router = APIRouter(tags=["Approvals"])


@router.get("", response_model=PaginatedResponse[ApprovalResponse])
def get_approvals(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
    status: ApprovalStatus | None = None,
) -> dict:
    """List approval requests."""
    skip = (params.page - 1) * params.size
    approvals, total = approval_service.list_approvals(db, skip=skip, limit=params.size, status=status)

    return {
        "items": approvals,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{approval_id}", response_model=ApprovalResponse)
def get_approval(
    approval_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> ApprovalRequest:
    """Get a specific approval request."""
    return approval_service.get_approval(db, approval_id)


@router.post("/{approval_id}/approve", response_model=ApprovalResponse)
def approve_request(
    approval_id: int,
    action_in: ApprovalActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> ApprovalRequest:
    """Approve a pending request (Analyst/Admin only)."""
    return approval_service.approve_request(db, approval_id, current_user.id, action_in)


@router.post("/{approval_id}/reject", response_model=ApprovalResponse)
def reject_request(
    approval_id: int,
    action_in: ApprovalActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> ApprovalRequest:
    """Reject a pending request (Analyst/Admin only)."""
    return approval_service.reject_request(db, approval_id, current_user.id, action_in)
