"""Health check API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.config import get_settings
from app.db.database import check_database_health

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    """Return the current health status of the SentinelX backend.

    Performs a real database connectivity check — does not fake "healthy"
    if the database is unreachable.

    Returns:
        JSON with service status, version, database health, and timestamp.
    """
    settings = get_settings()
    db_healthy = check_database_health()

    return {
        "status": "ok" if db_healthy else "degraded",
        "service": "sentinelx-backend",
        "version": settings.APP_VERSION,
        "database": "healthy" if db_healthy else "unhealthy",
        "timestamp": datetime.now(UTC).isoformat(),
    }
