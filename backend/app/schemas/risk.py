"""Risk assessment schemas — request/response models for the risk evaluation API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── Risk Context (input to the risk engine) ──────────────────────────────────

class SensitivityContext(BaseModel):
    """Sensitivity information from Phase 3 classification."""
    level: str = "UNKNOWN"
    categories: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    classifier_version: str | None = None


class ActionContext(BaseModel):
    """Details about the action being performed."""
    action_type: str = "UNKNOWN"
    event_type: str | None = None


class DestinationContext(BaseModel):
    """Details about the operation destination."""
    destination_type: str = "UNKNOWN"
    destination_identifier: str | None = None
    trust_level: str | None = None


class UserContext(BaseModel):
    """User context for risk assessment."""
    user_id: str | None = None
    user_role: str = "UNKNOWN"
    privilege_level: str | None = None
    authentication_status: str | None = None


class DeviceContext(BaseModel):
    """Device context for risk assessment."""
    device_id: str | None = None
    device_trust: str = "UNKNOWN"
    managed: bool = False
    security_status: str | None = None


class BehavioralContext(BaseModel):
    """Behavioral signals for risk assessment."""
    recent_sensitive_ops: int = 0
    recent_total_ops: int = 0
    time_window_seconds: int = 300
    rapid_operations: bool = False
    unusual_destination: bool = False
    multiple_sensitive_files: bool = False


class TimeContextInput(BaseModel):
    """Time context for risk assessment."""
    timestamp: datetime | None = None
    is_business_hours: bool | None = None
    is_weekend: bool | None = None


class VolumeContext(BaseModel):
    """Volume signals for risk assessment."""
    file_size_bytes: int = 0
    total_bytes_in_window: int = 0
    sensitive_files_in_window: int = 0
    operations_in_window: int = 0


class FileContext(BaseModel):
    """File metadata for context (no sensitive content)."""
    file_name: str | None = None
    file_hash: str | None = None
    file_size: int | None = None
    file_path: str | None = None


class RiskContextInput(BaseModel):
    """Complete risk context — used as input to POST /risk/evaluate."""
    event_id: str | None = None
    classification_id: int | None = None
    sensitivity: SensitivityContext = Field(default_factory=SensitivityContext)
    action: ActionContext = Field(default_factory=ActionContext)
    destination: DestinationContext = Field(default_factory=DestinationContext)
    user_context: UserContext = Field(default_factory=UserContext)
    device_context: DeviceContext = Field(default_factory=DeviceContext)
    behavioral_context: BehavioralContext = Field(default_factory=BehavioralContext)
    time_context: TimeContextInput = Field(default_factory=TimeContextInput)
    volume_context: VolumeContext = Field(default_factory=VolumeContext)
    file_context: FileContext = Field(default_factory=FileContext)
    process_name: str | None = None
    process_id: int | None = None


class RiskEvaluateRequest(BaseModel):
    """Minimal request to evaluate risk for an existing event + classification."""
    event_id: str
    classification_id: int | None = None


# ── Risk Factor (output component) ──────────────────────────────────────────

class RiskFactor(BaseModel):
    """A single risk factor in the breakdown."""
    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    contribution: float
    reason: str


# ── Risk Assessment (output) ────────────────────────────────────────────────

class RiskAssessmentResult(BaseModel):
    """Complete risk assessment result returned by the risk engine."""
    risk_score: float = Field(ge=0, le=100)
    risk_level: str
    factors: list[RiskFactor] = Field(default_factory=list)
    explanation: str = ""


class RiskAssessmentResponse(BaseModel):
    """API response for a completed risk assessment (includes persistence info)."""
    id: int
    risk_assessment_id: int  # alias for clarity
    event_id: str
    risk_score: float
    risk_level: str
    decision: str
    policy_id: int | None = None
    policy_name: str | None = None
    factors: list[RiskFactor] = Field(default_factory=list)
    explanation: str = ""
    risk_engine_version: str
    policy_engine_version: str
    risk_config_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentListResponse(BaseModel):
    """Minimal response for list queries."""
    id: int
    event_id: str
    risk_score: float
    risk_level: str
    decision: str
    policy_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Simulation ──────────────────────────────────────────────────────────────

class PolicySimulationRequest(BaseModel):
    """Request body for policy simulation against hypothetical context."""
    context: RiskContextInput


class PolicySimulationResponse(BaseModel):
    """Result of a policy simulation (no persistence, no enforcement)."""
    risk_score: float
    risk_level: str
    decision: str
    policy_id: int | None = None
    policy_name: str | None = None
    factors: list[RiskFactor] = Field(default_factory=list)
    matching_policies: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""
