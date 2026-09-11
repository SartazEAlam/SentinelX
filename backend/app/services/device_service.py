"""Device service for endpoint agent management."""

import secrets
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_device_token
from app.models.device import Device
from app.models.enums import AuditAction, DeviceStatus
from app.schemas.devices import (
    DeviceRegister,
    DeviceRegisterResponse,
    DeviceUpdate,
    HeartbeatRequest,
)
from app.services.audit_service import log_action


def get_device(db: Session, device_id: str) -> Device:
    """Get a device by its unique ID."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise NotFoundError("Device not found")
    return device


def list_devices(
    db: Session, skip: int = 0, limit: int = 50, status: DeviceStatus | None = None
) -> tuple[list[Device], int]:
    """List devices with optional filtering."""
    query = db.query(Device)
    if status:
        query = query.filter(Device.status == status)

    total = query.count()
    devices = query.offset(skip).limit(limit).all()
    return devices, total


def register_device(db: Session, device_in: DeviceRegister, ip_address: str | None = None) -> DeviceRegisterResponse:
    """Register a new device or overwrite an existing disabled one."""
    existing = db.query(Device).filter(Device.device_id == device_in.device_id).first()

    if existing:
        if existing.is_active:
            raise ConflictError("Device is already registered and active")
        else:
            # We allow re-registration of a previously deactivated device,
            # but we delete it and recreate to ensure clean state.
            db.delete(existing)
            db.commit()

    # Generate a strong, secure one-time plaintext token
    raw_secret = secrets.token_urlsafe(32)
    # The Bearer token the client uses will be `<device_id>.<secret>`
    full_token = f"{device_in.device_id}.{raw_secret}"

    hashed_token = hash_device_token(full_token)

    device = Device(
        device_id=device_in.device_id,
        device_name=device_in.device_name,
        hostname=device_in.hostname,
        operating_system=device_in.operating_system,
        os_version=device_in.os_version,
        agent_version=device_in.agent_version,
        ip_address=ip_address or device_in.ip_address,
        status=DeviceStatus.ONLINE,
        is_active=True,
        token_hash=hashed_token,
        last_seen_at=datetime.now(UTC),
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    log_action(
        db,
        action=AuditAction.DEVICE_REGISTERED,
        actor_device_id=device.device_id,
        resource_type="Device",
        resource_id=device.device_id,
        ip_address=ip_address,
    )

    return DeviceRegisterResponse(
        id=device.id,
        device_id=device.device_id,
        token=full_token,  # ONLY RETURNED ONCE!
        status=device.status,
        registered_at=device.registered_at,
    )


def update_device(
    db: Session, device_id: str, device_in: DeviceUpdate, actor_id: int | None = None
) -> Device:
    """Admin update of device fields."""
    device = get_device(db, device_id)

    if device_in.device_name is not None:
        device.device_name = device_in.device_name

    if device_in.is_active is not None:
        device.is_active = device_in.is_active
        if not device.is_active:
            device.status = DeviceStatus.DISABLED

    db.commit()
    db.refresh(device)

    log_action(
        db,
        action=AuditAction.DEVICE_UPDATED,
        actor_user_id=actor_id,
        resource_type="Device",
        resource_id=device.device_id,
    )

    return device


def enable_device(db: Session, device_id: str, actor_id: int | None = None) -> Device:
    """Re-enable a disabled device."""
    device = get_device(db, device_id)
    device.is_active = True
    device.status = DeviceStatus.ONLINE
    db.commit()
    db.refresh(device)

    log_action(
        db,
        action=AuditAction.DEVICE_ENABLED,
        actor_user_id=actor_id,
        resource_type="Device",
        resource_id=device.device_id,
    )
    return device


def disable_device(db: Session, device_id: str, actor_id: int | None = None) -> Device:
    """Disable an active device."""
    device = get_device(db, device_id)
    device.is_active = False
    device.status = DeviceStatus.DISABLED
    db.commit()
    db.refresh(device)

    log_action(
        db,
        action=AuditAction.DEVICE_DISABLED,
        actor_user_id=actor_id,
        resource_type="Device",
        resource_id=device.device_id,
    )
    return device


def record_heartbeat(
    db: Session, device_id: str, heartbeat: HeartbeatRequest, ip_address: str | None = None
) -> Device:
    """Record a heartbeat from an active device."""
    device = get_device(db, device_id)

    if not device.is_active:
        raise ConflictError("Cannot record heartbeat for disabled device")

    device.last_seen_at = datetime.now(UTC)
    device.status = DeviceStatus.ONLINE

    if heartbeat.agent_version:
        device.agent_version = heartbeat.agent_version
    if heartbeat.ip_address:
        device.ip_address = heartbeat.ip_address
    elif ip_address:
        device.ip_address = ip_address

    db.commit()
    db.refresh(device)

    # We do NOT log heartbeats to AuditLog, as they happen too frequently
    # and would bloat the database. They just update the `last_seen_at`.

    return device
