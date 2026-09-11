"""Main API router combining all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.alerts import router as alerts_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.audit import router as audit_router
from app.api.v1.auth import router as auth_router
from app.api.v1.devices import router as devices_router
from app.api.v1.events import router as events_router
from app.api.v1.policies import router as policies_router
from app.api.v1.stats import router as stats_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(users_router, prefix="/users")
api_router.include_router(devices_router, prefix="/devices")
api_router.include_router(events_router, prefix="/events")
api_router.include_router(approvals_router, prefix="/approvals")
api_router.include_router(policies_router, prefix="/policies")
api_router.include_router(alerts_router, prefix="/alerts")
api_router.include_router(audit_router, prefix="/audit")
api_router.include_router(stats_router, prefix="/stats")
