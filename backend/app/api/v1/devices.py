"""Device management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_device, require_analyst_or_above
from app.db.database import get_db
from app.models.device import Device
from app.models.enums import DeviceStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.devices import (
    DeviceRegister,
    DeviceRegisterResponse,
    DeviceResponse,
    DeviceUpdate,
    HeartbeatRequest,
)
from app.services import device_service

router = APIRouter(tags=["Devices"])


# Open endpoint: Agent uses this to register (Admin might also trigger it via deployment script)
@router.post("/register", response_model=DeviceRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    device_in: DeviceRegister,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> DeviceRegisterResponse:
    """Register a new endpoint device and obtain an authentication token."""
    ip_address = request.client.host if request.client else None
    return device_service.register_device(db, device_in, ip_address=ip_address)


# Device authenticated endpoints
@router.post("/heartbeat", response_model=DeviceResponse)
def heartbeat(
    heartbeat_in: HeartbeatRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_device: Annotated[Device, Depends(get_current_device)],
) -> Device:
    """Agent endpoint to report status and update last_seen_at."""
    ip_address = request.client.host if request.client else None
    return device_service.record_heartbeat(
        db, current_device.device_id, heartbeat_in, ip_address=ip_address
    )


# Analyst/Admin endpoints
@router.get("", response_model=PaginatedResponse[DeviceResponse])
def get_devices(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
    status: DeviceStatus | None = None,
) -> dict:
    """List registered devices."""
    skip = (params.page - 1) * params.size
    devices, total = device_service.list_devices(db, skip=skip, limit=params.size, status=status)
    
    return {
        "items": devices,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Device:
    """Get device details."""
    return device_service.get_device(db, device_id)


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: str,
    device_in: DeviceUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Device:
    """Update device metadata."""
    return device_service.update_device(db, device_id, device_in, actor_id=current_user.id)


@router.post("/{device_id}/enable", response_model=DeviceResponse)
def enable_device(
    device_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Device:
    """Re-enable a disabled device."""
    return device_service.enable_device(db, device_id, actor_id=current_user.id)


@router.post("/{device_id}/disable", response_model=DeviceResponse)
def disable_device(
    device_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Device:
    """Disable an active device."""
    return device_service.disable_device(db, device_id, actor_id=current_user.id)
