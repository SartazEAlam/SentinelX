"""Audit logging schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditAction


class AuditLogResponse(BaseModel):
    """Standard audit log representation in the API."""
    id: int
    actor_user_id: int | None
    actor_device_id: str | None
    action: AuditAction
    resource_type: str | None
    resource_id: str | None
    timestamp: datetime
    ip_address: str | None
    user_agent: str | None
    metadata_json: Any | None

    model_config = ConfigDict(from_attributes=True)
