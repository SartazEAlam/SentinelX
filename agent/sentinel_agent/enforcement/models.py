"""Enforcement data models — decisions, results, and operation metadata.

These are the agent-side models. The backend has corresponding DB models.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Decision(StrEnum):
    """Enforcement decisions produced by Phase 4."""

    ALLOW = "ALLOW"
    HOLD = "HOLD"
    BLOCK = "BLOCK"


class DestinationType(StrEnum):
    """Classification of operation destinations."""

    LOCAL_TRUSTED = "LOCAL_TRUSTED"
    LOCAL_UNTRUSTED = "LOCAL_UNTRUSTED"
    USB_TRUSTED = "USB_TRUSTED"
    USB_UNTRUSTED = "USB_UNTRUSTED"
    NETWORK_TRUSTED = "NETWORK_TRUSTED"
    NETWORK_UNTRUSTED = "NETWORK_UNTRUSTED"
    CLOUD = "CLOUD"
    UNKNOWN = "UNKNOWN"


class EnforcementStatus(StrEnum):
    """Final status of an enforcement operation."""

    ALLOWED = "ALLOWED"
    HELD = "HELD"
    BLOCKED = "BLOCKED"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EnforcementDecision(BaseModel):
    """A normalized enforcement decision received from the server.

    Bound to a specific event and risk assessment to prevent replay.
    """

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    risk_assessment_id: int | None = None
    decision: Decision
    policy_id: int | None = None
    policy_version: int | None = None
    risk_score: float = 0.0
    risk_level: str = "UNKNOWN"
    explanation: str = ""
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    source: str = "server"

    def is_expired(self) -> bool:
        """Check if this decision has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) >= self.expires_at

    def validate_binding(
        self,
        event_id: str,
        source_hash: str | None = None,
        destination: str | None = None,
    ) -> bool:
        """Validate that this decision is bound to the correct operation."""
        if self.event_id != event_id:
            return False
        return True


class EnforcementOperation(BaseModel):
    """Complete record of an enforcement operation."""

    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    decision: Decision | None = None
    state: str = "DETECTED"

    # Source info
    source_path: str = ""
    source_hash: str = ""
    file_name: str = ""
    file_size: int = 0

    # Destination info
    destination: str = ""
    destination_type: str = "UNKNOWN"

    # Risk info
    risk_assessment_id: int | None = None
    risk_score: float = 0.0
    risk_level: str = "UNKNOWN"
    policy_id: int | None = None
    policy_version: int | None = None

    # Approval info
    approval_id: str | None = None

    # Staging info
    staging_path: str | None = None
    staged_hash: str | None = None

    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None

    # Result
    error_code: str | None = None
    error_message: str | None = None
    destination_hash: str | None = None
    bytes_transferred: int = 0


class EnforcementResult(BaseModel):
    """Result of an enforcement action."""

    operation_id: str
    status: EnforcementStatus
    decision: Decision
    started_at: datetime | None = None
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_hash: str = ""
    destination_hash: str = ""
    bytes_transferred: int = 0
    reason_code: str = ""
    error_code: str = ""
    message: str = ""

    def to_api_dict(self) -> dict:
        """Convert to backend API format."""
        return {
            "operation_id": self.operation_id,
            "status": self.status.value,
            "decision": self.decision.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat(),
            "source_hash": self.source_hash,
            "destination_hash": self.destination_hash,
            "bytes_transferred": self.bytes_transferred,
            "reason_code": self.reason_code,
            "error_code": self.error_code,
            "message": self.message,
        }


class StagingRecord(BaseModel):
    """Metadata for a staged (held) file operation."""

    staging_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_id: str
    event_id: str
    source_path: str
    source_hash: str
    staging_path: str
    destination: str
    file_size: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    approval_id: str | None = None
    status: str = "STAGED"


class OfflineDecision(BaseModel):
    """Locally-determined decision when server is unavailable."""

    risk_level: str
    decision: Decision
    reason: str = "Server unavailable — applied offline policy"
