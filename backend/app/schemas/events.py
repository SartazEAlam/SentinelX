"""Security event schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EventDecision, EventType, SensitivityLevel


class SecurityEventCreate(BaseModel):
    """Payload sent by endpoint agents to report a security event."""
    event_id: str
    timestamp: datetime
    event_type: EventType
    action: str | None = None
    source: str | None = None
    destination: str | None = None
    file_name: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    file_hash: str | None = None
    sensitivity_level: SensitivityLevel | None = None
    risk_score: float | None = Field(default=None, ge=0.0, le=100.0)
    decision: EventDecision | None = None
    status: str | None = None
    user_context: str | None = None
    process_name: str | None = None
    process_id: int | None = None
    metadata_json: dict[str, Any] | None = None


class BatchEventCreate(BaseModel):
    """Batch payload of multiple security events."""
    events: list[SecurityEventCreate]

    @field_validator("events")
    @classmethod
    def validate_batch_size(cls, v: list[SecurityEventCreate]) -> list[SecurityEventCreate]:
        # Config max batch size is validated in the service layer,
        # but we add a hard ceiling here to prevent memory exhaustion
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 events")
        return v


class BatchEventResponse(BaseModel):
    """Result of a batch ingestion operation."""
    accepted: int
    rejected: int
    errors: list[dict[str, Any]] | None = None


class SecurityEventResponse(BaseModel):
    """Standard security event representation in the API."""
    id: int
    event_id: str
    device_id: str
    timestamp: datetime
    event_type: EventType
    action: str | None
    source: str | None
    destination: str | None
    file_name: str | None
    file_path: str | None
    file_size: int | None
    file_hash: str | None
    sensitivity_level: SensitivityLevel | None
    risk_score: float | None
    decision: EventDecision | None
    status: str | None
    user_context: str | None
    process_name: str | None
    process_id: int | None
    metadata_json: Any | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
