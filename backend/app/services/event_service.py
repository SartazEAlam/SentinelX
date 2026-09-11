"""Security event service for ingestion and querying."""

import json

from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction, DeviceStatus, EventType, SensitivityLevel
from app.models.security_event import SecurityEvent
from app.schemas.events import BatchEventCreate, BatchEventResponse, SecurityEventCreate
from app.services.audit_service import log_action
from app.services.device_service import get_device


def get_event(db: Session, event_id: str) -> SecurityEvent:
    """Get a single security event by its event_id."""
    event = db.query(SecurityEvent).filter(SecurityEvent.event_id == event_id).first()
    if not event:
        raise NotFoundError("Event not found")
    return event


def list_events(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    device_id: str | None = None,
    event_type: EventType | None = None,
    sensitivity_level: SensitivityLevel | None = None,
    min_risk_score: float | None = None,
) -> tuple[list[SecurityEvent], int]:
    """List security events with optional filtering and pagination."""
    query = db.query(SecurityEvent)

    if device_id:
        query = query.filter(SecurityEvent.device_id == device_id)
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if sensitivity_level:
        query = query.filter(SecurityEvent.sensitivity_level == sensitivity_level)
    if min_risk_score is not None:
        query = query.filter(SecurityEvent.risk_score >= min_risk_score)

    total = query.count()
    events = query.order_by(desc(SecurityEvent.timestamp)).offset(skip).limit(limit).all()
    return events, total


def create_event(
    db: Session, device_id: str, event_in: SecurityEventCreate, log_audit: bool = True
) -> SecurityEvent:
    """Ingest a single security event."""
    device = get_device(db, device_id)
    if not device.is_active or device.status == DeviceStatus.DISABLED:
        raise ConflictError("Device is disabled")

    metadata_json = json.dumps(event_in.metadata_json) if event_in.metadata_json else None

    event = SecurityEvent(
        event_id=event_in.event_id,
        device_id=device.device_id,
        timestamp=event_in.timestamp,
        event_type=event_in.event_type,
        action=event_in.action,
        source=event_in.source,
        destination=event_in.destination,
        file_name=event_in.file_name,
        file_path=event_in.file_path,
        file_size=event_in.file_size,
        file_hash=event_in.file_hash,
        sensitivity_level=event_in.sensitivity_level,
        risk_score=event_in.risk_score,
        decision=event_in.decision,
        status=event_in.status,
        user_context=event_in.user_context,
        process_name=event_in.process_name,
        process_id=event_in.process_id,
        metadata_json=metadata_json,
    )

    try:
        db.add(event)
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"Event with id {event.event_id} already exists")

    if log_audit:
        log_action(
            db,
            action=AuditAction.EVENT_CREATED,
            actor_device_id=device.device_id,
            resource_type="SecurityEvent",
            resource_id=event.event_id,
        )

    return event


def create_events_batch(
    db: Session, device_id: str, batch_in: BatchEventCreate
) -> BatchEventResponse:
    """Ingest a batch of security events from a device.
    
    Processing is all-or-nothing for the batch to ensure consistency.
    """
    settings = get_settings()
    if len(batch_in.events) > settings.MAX_BATCH_SIZE:
        raise ConflictError(f"Batch size exceeds maximum of {settings.MAX_BATCH_SIZE}")

    device = get_device(db, device_id)
    if not device.is_active or device.status == DeviceStatus.DISABLED:
        raise ConflictError("Device is disabled")

    accepted = 0
    errors = []

    for event_in in batch_in.events:
        metadata_json = json.dumps(event_in.metadata_json) if event_in.metadata_json else None
        
        event = SecurityEvent(
            event_id=event_in.event_id,
            device_id=device.device_id,
            timestamp=event_in.timestamp,
            event_type=event_in.event_type,
            action=event_in.action,
            source=event_in.source,
            destination=event_in.destination,
            file_name=event_in.file_name,
            file_path=event_in.file_path,
            file_size=event_in.file_size,
            file_hash=event_in.file_hash,
            sensitivity_level=event_in.sensitivity_level,
            risk_score=event_in.risk_score,
            decision=event_in.decision,
            status=event_in.status,
            user_context=event_in.user_context,
            process_name=event_in.process_name,
            process_id=event_in.process_id,
            metadata_json=metadata_json,
        )
        db.add(event)
        accepted += 1

    try:
        db.commit()
        log_action(
            db,
            action=AuditAction.EVENT_BATCH_CREATED,
            actor_device_id=device.device_id,
            resource_type="SecurityEvent",
            metadata={"batch_size": accepted},
        )
    except IntegrityError as e:
        db.rollback()
        # If any event fails, the whole batch fails
        return BatchEventResponse(
            accepted=0,
            rejected=len(batch_in.events),
            errors=[{"message": "Integrity error (possible duplicate event_id)", "detail": str(e)}],
        )

    return BatchEventResponse(accepted=accepted, rejected=0)
