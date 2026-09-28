"""Pydantic schemas for the SentinelX API."""

from app.schemas.alerts import AlertActionRequest, AlertResponse
from app.schemas.approvals import ApprovalActionRequest, ApprovalCreate, ApprovalResponse
from app.schemas.audit import AuditLogResponse
from app.schemas.auth import LoginRequest, TokenResponse, UserMeResponse
from app.schemas.common import ErrorDetail, ErrorResponse, PaginatedResponse, PaginationParams
from app.schemas.devices import (
    DeviceRegister,
    DeviceRegisterResponse,
    DeviceResponse,
    DeviceUpdate,
    HeartbeatRequest,
)
from app.schemas.events import (
    BatchEventCreate,
    BatchEventResponse,
    SecurityEventCreate,
    SecurityEventResponse,
)
from app.schemas.policies import PolicyCreate, PolicyResponse, PolicyUpdate
from app.schemas.risk import (
    PolicySimulationRequest,
    PolicySimulationResponse,
    RiskAssessmentListResponse,
    RiskAssessmentResponse,
    RiskContextInput,
    RiskEvaluateRequest,
    RiskFactor,
)
from app.schemas.stats import EventTrend, OverviewStats
from app.schemas.users import UserCreate, UserResponse, UserUpdate

__all__ = [
    # Common
    "ErrorDetail",
    "ErrorResponse",
    "PaginatedResponse",
    "PaginationParams",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "UserMeResponse",
    # Users
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Devices
    "DeviceRegister",
    "DeviceRegisterResponse",
    "DeviceResponse",
    "DeviceUpdate",
    "HeartbeatRequest",
    # Events
    "BatchEventCreate",
    "BatchEventResponse",
    "SecurityEventCreate",
    "SecurityEventResponse",
    # Approvals
    "ApprovalActionRequest",
    "ApprovalCreate",
    "ApprovalResponse",
    # Policies
    "PolicyCreate",
    "PolicyResponse",
    "PolicyUpdate",
    # Risk (Phase 4)
    "RiskAssessmentListResponse",
    "RiskAssessmentResponse",
    "RiskContextInput",
    "RiskEvaluateRequest",
    "RiskFactor",
    "PolicySimulationRequest",
    "PolicySimulationResponse",
    # Alerts
    "AlertActionRequest",
    "AlertResponse",
    # Audit
    "AuditLogResponse",
    # Stats
    "EventTrend",
    "OverviewStats",
]
