"""Security event routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_device, require_viewer_or_above
from app.db.database import get_db
from app.models.device import Device
from app.models.enums import EventType, SensitivityLevel
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.events import (
    BatchEventCreate,
    BatchEventResponse,
    SecurityEventCreate,
    SecurityEventResponse,
)
from app.services import event_service

router = APIRouter(tags=["Events"])


# Device authenticated endpoints (Agent ingestion)
@router.post("", response_model=SecurityEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_in: SecurityEventCreate,
    db: Annotated[Session, Depends(get_db)],
    current_device: Annotated[Device, Depends(get_current_device)],
) -> SecurityEvent:
    """Ingest a single security event from an authenticated endpoint agent."""
    return event_service.create_event(db, current_device.device_id, event_in)


@router.post("/batch", response_model=BatchEventResponse, status_code=status.HTTP_201_CREATED)
def create_events_batch(
    batch_in: BatchEventCreate,
    db: Annotated[Session, Depends(get_db)],
    current_device: Annotated[Device, Depends(get_current_device)],
) -> BatchEventResponse:
    """Ingest a batch of security events from an authenticated endpoint agent."""
    return event_service.create_events_batch(db, current_device.device_id, batch_in)


# Analyst/Viewer endpoints (Dashboard)
@router.get("", response_model=PaginatedResponse[SecurityEventResponse])
def get_events(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
    device_id: str | None = Query(default=None, description="Filter by device ID"),
    event_type: EventType | None = Query(default=None, description="Filter by event type"),
    sensitivity_level: SensitivityLevel | None = Query(default=None, description="Filter by sensitivity"),
    min_risk_score: float | None = Query(default=None, description="Minimum risk score"),
) -> dict:
    """List security events with filtering (Viewer/Analyst/Admin)."""
    skip = (params.page - 1) * params.size
    events, total = event_service.list_events(
        db,
        skip=skip,
        limit=params.size,
        device_id=device_id,
        event_type=event_type,
        sensitivity_level=sensitivity_level,
        min_risk_score=min_risk_score,
    )

    return {
        "items": events,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{event_id}", response_model=SecurityEventResponse)
def get_event(
    event_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> SecurityEvent:
    """Get a specific security event by ID."""
    return event_service.get_event(db, event_id)
