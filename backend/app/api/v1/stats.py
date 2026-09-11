"""Dashboard statistics routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_viewer_or_above
from app.db.database import get_db
from app.models.user import User
from app.schemas.stats import OverviewStats
from app.services import stats_service

router = APIRouter(tags=["Statistics"])


@router.get("/overview", response_model=OverviewStats)
def get_dashboard_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_viewer_or_above)],
) -> OverviewStats:
    """Get aggregated metrics for the SentinelX dashboard."""
    return stats_service.get_overview_stats(db)
