"""Approval workflow schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalStatus
from app.schemas.users import UserResponse


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

    # Nested relationships
    requester: UserResponse | None = None
    reviewer: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
