"""Alert management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_analyst_or_above, require_viewer_or_above
from app.db.database import get_db
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertStatus
from app.models.user import User
from app.schemas.alerts import AlertActionRequest, AlertResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services import alert_service

router = APIRouter(tags=["Alerts"])


@router.get("", response_model=PaginatedResponse[AlertResponse])
def get_alerts(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
    status: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    device_id: str | None = None,
) -> dict:
    """List security alerts."""
    skip = (params.page - 1) * params.size
    alerts, total = alert_service.list_alerts(
        db, skip=skip, limit=params.size, status=status, severity=severity, device_id=device_id
    )

    return {
        "items": alerts,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> Alert:
    """Get a specific alert."""
    return alert_service.get_alert(db, alert_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(
    alert_id: int,
    action_in: AlertActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Alert:
    """Acknowledge an alert (Analyst/Admin)."""
    return alert_service.acknowledge_alert(db, alert_id, current_user.id, action_in)


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    action_in: AlertActionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> Alert:
    """Resolve an alert (Analyst/Admin)."""
    return alert_service.resolve_alert(db, alert_id, current_user.id, action_in)
