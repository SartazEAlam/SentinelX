"""Pydantic schemas for enforcement API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EnforcementResultCreate(BaseModel):
    """Payload sent by the agent to report an enforcement result."""

    operation_id: str
    status: str
    decision: str
    started_at: datetime | None = None
    completed_at: datetime
    source_hash: str | None = None
    destination_hash: str | None = None
    bytes_transferred: int = 0
    reason_code: str | None = None
    error_code: str | None = None
    message: str | None = None


class EnforcementResultResponse(EnforcementResultCreate):
    """Response model for an enforcement result."""

    id: int

    model_config = ConfigDict(from_attributes=True)
