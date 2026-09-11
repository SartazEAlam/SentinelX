"""Audit log routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.db.database import get_db
from app.models.enums import AuditAction
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services import audit_service

router = APIRouter(tags=["Audit Logs"])


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def get_audit_logs(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
    action: AuditAction | None = None,
    actor_user_id: int | None = None,
    actor_device_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> dict:
    """List system audit logs (Admin only)."""
    skip = (params.page - 1) * params.size
    logs, total = audit_service.list_audit_logs(
        db,
        skip=skip,
        limit=params.size,
        action=action,
        actor_user_id=actor_user_id,
        actor_device_id=actor_device_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )

    return {
        "items": logs,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }
