"""Risk assessment API routes — Phase 4.

Endpoints:
  POST /api/v1/risk/evaluate       — Evaluate risk for an existing event
  GET  /api/v1/risk/assessments     — List risk assessments
  GET  /api/v1/risk/assessments/{id} — Get a specific risk assessment
"""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user_or_device,
    require_analyst_or_above,
    require_viewer_or_above,
)
from fastapi import APIRouter, Depends, Query, status
from app.models.device import Device
from app.db.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.risk import (
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    RiskEvaluateRequest,
    RiskFactor,
)
from app.services import policy_evaluator

router = APIRouter(tags=["Risk Assessment"])


@router.post(
    "/evaluate",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate risk for a security event",
    description=(
        "Run the risk engine and policy engine against an existing event. "
        "The server loads the event and classification from the database — "
        "client-provided risk values are not trusted."
    ),
)
def evaluate_risk(
    request: RiskEvaluateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_actor: Annotated[User | Device, Depends(get_current_user_or_device)],
) -> RiskAssessmentResponse:
    """Evaluate the risk of an existing security event (Agent API or User API)."""
    actor_id = current_actor.id if isinstance(current_actor, User) else None
    return policy_evaluator.evaluate_event(
        db,
        event_id=request.event_id,
        classification_id=request.classification_id,
        actor_user_id=actor_id,
    )


@router.get(
    "/assessments",
    response_model=PaginatedResponse[RiskAssessmentListResponse],
    summary="List risk assessments",
)
def list_assessments(
    params: Annotated[PaginationParams, Depends()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
    event_id: str | None = Query(default=None, description="Filter by event ID"),
    risk_level: str | None = Query(default=None, description="Filter by risk level"),
    decision: str | None = Query(default=None, description="Filter by decision"),
) -> dict[str, Any]:
    """List risk assessments with filtering and pagination."""
    skip = (params.page - 1) * params.size
    assessments, total = policy_evaluator.list_risk_assessments(
        db, skip=skip, limit=params.size,
        event_id=event_id, risk_level=risk_level, decision=decision,
    )

    items = []
    for a in assessments:
        items.append(RiskAssessmentListResponse(
            id=a.id,
            event_id=a.event_id,
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            decision=a.decision,
            policy_name=a.policy_name,
            created_at=a.created_at,
        ))

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "size": params.size,
        "pages": (total + params.size - 1) // params.size if total > 0 else 0,
    }


@router.get(
    "/assessments/{assessment_id}",
    response_model=RiskAssessmentResponse,
    summary="Get a specific risk assessment",
)
def get_assessment(
    assessment_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> RiskAssessmentResponse:
    """Get a specific risk assessment by ID."""
    record = policy_evaluator.get_risk_assessment(db, assessment_id)

    # Parse stored factor breakdown
    factors: list[RiskFactor] = []
    if record.factor_breakdown_json:
        try:
            raw_factors = json.loads(record.factor_breakdown_json)
            for f in raw_factors:
                factors.append(RiskFactor(**f))
        except (json.JSONDecodeError, TypeError):
            pass

    return RiskAssessmentResponse(
        id=record.id,
        risk_assessment_id=record.id,
        event_id=record.event_id,
        risk_score=record.risk_score,
        risk_level=record.risk_level,
        decision=record.decision,
        policy_id=record.policy_id,
        policy_name=record.policy_name,
        factors=factors,
        explanation=record.explanation or "",
        risk_engine_version=record.risk_engine_version,
        policy_engine_version=record.policy_engine_version,
        risk_config_version=record.risk_config_version,
        created_at=record.created_at,
    )
