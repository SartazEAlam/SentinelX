"""Alert management schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertStatus
from app.schemas.users import UserResponse


class AlertActionRequest(BaseModel):
    """Payload for acknowledging or resolving an alert."""
    comment: str | None = None


class AlertResponse(BaseModel):
    """Standard alert representation in the API."""
    id: int
    alert_id: str
    event_id: int | None
    device_id: str | None
    severity: AlertSeverity
    title: str
    message: str | None
    status: AlertStatus
    
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    # Nested relationships
    acknowledger: UserResponse | None = None
    resolver: UserResponse | None = None

    model_config = ConfigDict(from_attributes=True)
