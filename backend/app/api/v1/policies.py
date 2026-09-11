"""Policy management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_viewer_or_above
from app.db.database import get_db
from app.models.policy import Policy
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.policies import PolicyCreate, PolicyResponse, PolicyUpdate
from app.services import policy_service

router = APIRouter(tags=["Policies"])


@router.get("", response_model=PaginatedResponse[PolicyResponse])
def get_policies(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> dict:
    """List DLP policies."""
    skip = (params.page - 1) * params.size
    policies, total = policy_service.list_policies(db, skip=skip, limit=params.size)
    
    return {
        "items": policies,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size,
    }


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> Policy:
    """Get a specific policy."""
    return policy_service.get_policy(db, policy_id)


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    policy_in: PolicyCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Policy:
    """Create a new policy (Admin only)."""
    return policy_service.create_policy(db, policy_in, current_user.id)


@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_policy(
    policy_id: int,
    policy_in: PolicyUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Policy:
    """Update an existing policy (Admin only)."""
    return policy_service.update_policy(db, policy_id, policy_in, current_user.id)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(
    policy_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    """Delete a policy (Admin only)."""
    policy_service.delete_policy(db, policy_id, current_user.id)
