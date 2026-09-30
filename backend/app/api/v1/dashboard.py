"""Dashboard API routes — Phase 6.

Provides aggregated dashboard data endpoints for the administrator UI.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_viewer_or_above
from app.db.database import get_db
from app.models.user import User
from app.schemas.stats import (
    DashboardSummary,
    EnforcementStats,
    OverviewStats,
    RiskDistribution,
    SensitivityDistribution,
)
from app.services import stats_service

router = APIRouter(tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> DashboardSummary:
    """Get main dashboard summary cards."""
    return stats_service.get_dashboard_summary(db)


@router.get("/overview", response_model=OverviewStats)
def get_dashboard_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> OverviewStats:
    """Get full overview statistics including trends."""
    return stats_service.get_overview_stats(db)


@router.get("/risk-distribution", response_model=RiskDistribution)
def get_risk_distribution(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
    period: str = Query(default="24h", description="Time period: 24h, 7d, 30d"),
) -> RiskDistribution:
    """Get risk level distribution."""
    return stats_service.get_risk_distribution(db, period=period)


@router.get("/sensitivity-distribution", response_model=SensitivityDistribution)
def get_sensitivity_distribution(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> SensitivityDistribution:
    """Get data sensitivity category distribution."""
    return stats_service.get_sensitivity_distribution(db)


@router.get("/enforcement-stats", response_model=EnforcementStats)
def get_enforcement_stats(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> EnforcementStats:
    """Get enforcement outcome statistics."""
    return stats_service.get_enforcement_stats(db)
