"""Audit service for creating and querying audit logs."""

import json
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import AuditAction


def log_action(
    db: Session,
    action: AuditAction,
    actor_user_id: int | None = None,
    actor_device_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Create a new append-only audit log entry."""

    metadata_json = json.dumps(metadata) if metadata else None

    audit_entry = AuditLog(
        action=action,
        actor_user_id=actor_user_id,
        actor_device_id=actor_device_id,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json,
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry


def list_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    action: AuditAction | None = None,
    actor_user_id: int | None = None,
    actor_device_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> tuple[list[AuditLog], int]:
    """Retrieve audit logs with optional filtering and pagination."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if actor_user_id:
        query = query.filter(AuditLog.actor_user_id == actor_user_id)
    if actor_device_id:
        query = query.filter(AuditLog.actor_device_id == actor_device_id)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.filter(AuditLog.resource_id == str(resource_id))

    total = query.count()
    logs = query.order_by(desc(AuditLog.timestamp)).offset(skip).limit(limit).all()

    return logs, total
