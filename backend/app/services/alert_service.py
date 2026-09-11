"""Alert service."""

from datetime import UTC, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertStatus, AuditAction
from app.schemas.alerts import AlertActionRequest
from app.services.audit_service import log_action


def get_alert(db: Session, alert_id: int) -> Alert:
    """Get an alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise NotFoundError("Alert not found")
    return alert


def list_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: AlertStatus | None = None,
    severity: AlertSeverity | None = None,
    device_id: str | None = None,
) -> tuple[list[Alert], int]:
    """List alerts with optional filtering."""
    query = db.query(Alert)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if device_id:
        query = query.filter(Alert.device_id == device_id)

    total = query.count()
    alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()

    return alerts, total


def acknowledge_alert(
    db: Session, alert_id: int, actor_id: int, action_in: AlertActionRequest
) -> Alert:
    """Acknowledge an open alert."""
    alert = get_alert(db, alert_id)
    if alert.status != AlertStatus.OPEN:
        raise ConflictError(f"Cannot acknowledge alert with status {alert.status}")

    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = actor_id
    alert.acknowledged_at = datetime.now(UTC)
    
    if action_in.comment:
        # We append comment to the message for now
        alert.message = f"{alert.message}\n\nAcknowledgment Note: {action_in.comment}"

    db.commit()
    db.refresh(alert)

    log_action(
        db,
        action=AuditAction.ALERT_ACKNOWLEDGED,
        actor_user_id=actor_id,
        resource_type="Alert",
        resource_id=alert.alert_id,
    )
    return alert


def resolve_alert(
    db: Session, alert_id: int, actor_id: int, action_in: AlertActionRequest
) -> Alert:
    """Resolve an open or acknowledged alert."""
    alert = get_alert(db, alert_id)
    if alert.status == AlertStatus.RESOLVED:
        raise ConflictError("Alert is already resolved")

    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = actor_id
    alert.resolved_at = datetime.now(UTC)
    
    if action_in.comment:
        # We append comment to the message for now
        alert.message = f"{alert.message}\n\nResolution Note: {action_in.comment}"

    db.commit()
    db.refresh(alert)

    log_action(
        db,
        action=AuditAction.ALERT_RESOLVED,
        actor_user_id=actor_id,
        resource_type="Alert",
        resource_id=alert.alert_id,
    )
    return alert
