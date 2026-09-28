"""Policy management routes — enhanced for Phase 4.

Phase 4 additions:
  - POST /policies/{id}/enable — enable a policy
  - POST /policies/{id}/disable — disable a policy
  - POST /policies/simulate — simulate policy evaluation
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_analyst_or_above, require_viewer_or_above
from app.db.database import get_db
from app.models.policy import Policy
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.policies import PolicyCreate, PolicyResponse, PolicyUpdate
from app.schemas.risk import PolicySimulationRequest, PolicySimulationResponse
from app.services import policy_service
from app.services.policy_evaluator import simulate_policy

router = APIRouter(tags=["Policies"])


@router.get("", response_model=PaginatedResponse[PolicyResponse])
def get_policies(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> dict[str, Any]:
    """List DLP policies."""
    skip = (params.page - 1) * params.size
    policies, total = policy_service.list_policies(db, skip=skip, limit=params.size)

    return {
        "items": policies,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size if total > 0 else 0,
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
    """Soft-delete a policy (Admin only)."""
    policy_service.delete_policy(db, policy_id, current_user.id)


@router.post("/{policy_id}/enable", response_model=PolicyResponse)
def enable_policy(
    policy_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Policy:
    """Enable a policy (Admin only)."""
    return policy_service.enable_policy(db, policy_id, current_user.id)


@router.post("/{policy_id}/disable", response_model=PolicyResponse)
def disable_policy(
    policy_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> Policy:
    """Disable a policy (Admin only)."""
    return policy_service.disable_policy(db, policy_id, current_user.id)


@router.post(
    "/simulate",
    response_model=PolicySimulationResponse,
    summary="Simulate policy evaluation",
    description=(
        "Evaluate a hypothetical event/classification against current policies "
        "without enforcing or persisting anything."
    ),
)
def simulate_policies(
    sim_request: PolicySimulationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_analyst_or_above)],
) -> PolicySimulationResponse:
    """Simulate policy evaluation for a hypothetical scenario."""
    result = simulate_policy(db, sim_request.context, actor_user_id=current_user.id)
    return PolicySimulationResponse(**result)
