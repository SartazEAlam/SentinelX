"""Pydantic schemas for enforcement API endpoints."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EnforcementResultCreate(BaseModel):
    """Payload sent by the agent to report an enforcement result."""

    operation_id: str
    status: str
    decision: str
    started_at: Optional[datetime] = None
    completed_at: datetime
    source_hash: Optional[str] = None
    destination_hash: Optional[str] = None
    bytes_transferred: int = 0
    reason_code: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None


class EnforcementResultResponse(EnforcementResultCreate):
    """Response model for an enforcement result."""

    id: int

    model_config = ConfigDict(from_attributes=True)
