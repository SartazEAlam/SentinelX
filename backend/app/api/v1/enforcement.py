"""Enforcement endpoints for the SentinelX API."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.dependencies import get_current_user
from app.schemas.enforcement import EnforcementResultCreate, EnforcementResultResponse
from app.services import enforcement_service

router = APIRouter()


@router.post("/results", response_model=EnforcementResultResponse)
def report_enforcement_result(
    result_in: EnforcementResultCreate,
    db: Session = Depends(get_db),
    # In a real system, this would be authenticated via Agent API token.
    # For now, using standard dependency for simplicity or bypassing.
) -> EnforcementResultResponse:
    """Report the final outcome of an enforcement operation from an agent."""
    return enforcement_service.create_enforcement_result(db=db, result_in=result_in)


@router.get("/results", response_model=list[EnforcementResultResponse])
def get_enforcement_results(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[EnforcementResultResponse]:
    """Retrieve all enforcement results."""
    return enforcement_service.get_enforcement_results(db=db, skip=skip, limit=limit)
