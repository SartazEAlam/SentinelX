"""Approval workflow schemas — enhanced for Phase 4.

Phase 4 adds risk_assessment_id and policy linkage to approvals.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus
from app.schemas.users import UserResponse


class ApprovalCreate(BaseModel):
    """Payload for requesting an approval for a security event."""

    event_id: int
    reason: str | None = None
    risk_assessment_id: int | None = None
    requested_action: str | None = None
    policy_id: int | None = None
    policy_version: int | None = None


class ApprovalActionRequest(BaseModel):
    """Payload for approving or rejecting a request."""

    comment: str | None = None


class ApprovalResponse(BaseModel):
    """Standard approval request representation in the API."""

    id: int
    request_id: str
    event_id: int
    status: ApprovalStatus
    reason: str | None
    reviewer_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None

    # Phase 4 additions
    risk_assessment_id: int | None = None
    requested_action: str | None = None
    expires_at: datetime | None = None
    policy_id: int | None = None
    policy_version: int | None = None

    # Nested relationships
    requester: UserResponse | None = None
    reviewer: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
