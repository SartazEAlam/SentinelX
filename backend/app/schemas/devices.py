"""Device management schemas."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DeviceStatus


class DeviceRegister(BaseModel):
    """Payload sent by endpoint agents to register."""
    device_id: str = Field(..., description="Unique hardware/OS identifier for the device")
    device_name: str
    hostname: str | None = None
    operating_system: str | None = None
    os_version: str | None = None
    agent_version: str | None = None
    ip_address: str | None = None


class DeviceRegisterResponse(BaseModel):
    """Response returned upon successful registration.
    
    Contains the one-time plaintext token that the agent must save
    and use as a Bearer token for subsequent requests.
    """
    id: int
    device_id: str
    token: str = Field(..., description="One-time plaintext token. Save this securely.")
    status: DeviceStatus
    registered_at: datetime


class DeviceUpdate(BaseModel):
    """Fields an admin can update on a device."""
    device_name: str | None = None
    is_active: bool | None = None


class HeartbeatRequest(BaseModel):
    """Payload sent by agents periodically to report status."""
    agent_version: str | None = None
    ip_address: str | None = None


class DeviceResponse(BaseModel):
    """Standard device representation in the API."""
    id: int
    device_id: str
    device_name: str
    hostname: str | None
    operating_system: str | None
    os_version: str | None
    agent_version: str | None
    ip_address: str | None
    status: DeviceStatus
    last_seen_at: datetime | None
    registered_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
