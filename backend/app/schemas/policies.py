"""Policy management schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EventDecision
from app.schemas.users import UserResponse


class PolicyCreate(BaseModel):
    """Payload for creating a new DLP policy."""
    name: str = Field(..., min_length=3, max_length=128)
    description: str | None = None
    enabled: bool = True
    priority: int = Field(default=100, ge=1)

    # JSON payloads for criteria
    sensitivity_levels: list[str] | None = None
    risk_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    allowed_actions: list[str] | None = None
    decision: EventDecision | None = None
    conditions: dict[str, Any] | None = None


class PolicyUpdate(BaseModel):
    """Payload for updating an existing DLP policy."""
    name: str | None = Field(default=None, min_length=3, max_length=128)
    description: str | None = None
    enabled: bool | None = None
    priority: int | None = Field(default=None, ge=1)
    sensitivity_levels: list[str] | None = None
    risk_threshold: float | None = Field(default=None, ge=0.0, le=100.0)
    allowed_actions: list[str] | None = None
    decision: EventDecision | None = None
    conditions: dict[str, Any] | None = None


class PolicyResponse(BaseModel):
    """Standard policy representation in the API."""
    id: int
    name: str
    description: str | None
    enabled: bool
    priority: int

    sensitivity_levels: Any | None
    risk_threshold: float | None
    allowed_actions: Any | None
    decision: EventDecision | None
    conditions: Any | None

    created_at: datetime
    updated_at: datetime

    # Nested relationship
    creator: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
