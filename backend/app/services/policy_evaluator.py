"""Policy evaluator — orchestrates risk engine + policy engine + persistence.

This is the high-level service that the API layer calls.  It:
  1. Loads event and classification data from the database
  2. Builds a RiskContext from real Phase 2/3 data
  3. Runs the risk engine
  4. Loads active policies from the database
  5. Runs the policy engine
  6. Persists the RiskAssessment
  7. Creates an ApprovalRequest if decision is HOLD
  8. Logs audit events
  9. Returns a structured result
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.approval import ApprovalRequest
from app.models.classification import Classification
from app.models.enums import ApprovalStatus, AuditAction
from app.models.policy import Policy
from app.models.risk_assessment import RiskAssessment
from app.models.security_event import SecurityEvent
from app.risk_policy_config.policy_config import get_default_policy_config
from app.risk_policy_config.risk_config import get_default_risk_config
from app.schemas.risk import (
    RiskAssessmentResponse,
    RiskContextInput,
    RiskFactor,
)
from app.services.audit_service import log_action
from app.services.policy_engine import PolicyDecision, PolicyEngine, PolicyRule
from app.services.risk_engine import RiskAssessmentOutput, RiskContext, RiskEngine

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  Singletons (re-created if config changes)
# ═════════════════════════════════════════════════════════════════════════════

_risk_engine: RiskEngine | None = None
_policy_engine: PolicyEngine | None = None


def _get_risk_engine() -> RiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine(get_default_risk_config())
    return _risk_engine


def _get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine(get_default_policy_config())
    return _policy_engine


# ═════════════════════════════════════════════════════════════════════════════
#  Event adapter — build RiskContext from Phase 2 event + Phase 3 classification
# ═════════════════════════════════════════════════════════════════════════════

def _map_event_type_to_action(event_type: str | None, action: str | None) -> str:
    """Map Phase 2 event_type / action to a Phase 4 ActionType string."""
    if action:
        return action.upper()

    mapping = {
        "FILE_ACCESS": "READ",
        "FILE_COPY": "COPY",
        "FILE_MOVE": "MOVE",
        "FILE_UPLOAD": "EXTERNAL_UPLOAD",
        "FILE_DOWNLOAD": "READ",
        "USB_ACTIVITY": "USB_TRANSFER",
        "NETWORK_TRANSFER": "NETWORK_TRANSFER",
        "CLOUD_SYNC": "CLOUD_SYNC",
        "EMAIL_ATTACHMENT": "EXTERNAL_UPLOAD",
        "CLIPBOARD_ACTIVITY": "COPY",
        "PROCESS_ACTIVITY": "READ",
        "OTHER": "UNKNOWN",
    }
    if event_type:
        return mapping.get(event_type.upper(), "UNKNOWN")
    return "UNKNOWN"


def _infer_destination_type(destination: str | None, event_type: str | None) -> str:
    """Best-effort inference of destination type from event metadata."""
    if not destination:
        if event_type:
            et = event_type.upper()
            if et == "USB_ACTIVITY":
                return "USB_UNTRUSTED"
            if et in ("FILE_UPLOAD", "EMAIL_ATTACHMENT"):
                return "EXTERNAL_NETWORK"
            if et == "CLOUD_SYNC":
                return "PUBLIC_CLOUD"
            if et == "NETWORK_TRANSFER":
                return "UNKNOWN_NETWORK"
        return "UNKNOWN"

    dest_lower = destination.lower()

    # USB detection
    if any(marker in dest_lower for marker in ["usb", "removable", ":\\e\\", ":\\f\\", ":\\g\\"]):
        return "USB_UNTRUSTED"

    # Network paths
    if dest_lower.startswith("\\\\") or dest_lower.startswith("//"):
        return "UNKNOWN_NETWORK"

    # Cloud indicators
    cloud_markers = ["dropbox", "onedrive", "gdrive", "google drive", "icloud", "s3://", "azure"]
    if any(marker in dest_lower for marker in cloud_markers):
        return "PUBLIC_CLOUD"

    # HTTP URLs
    if dest_lower.startswith("http://") or dest_lower.startswith("https://"):
        return "EXTERNAL_NETWORK"

    # Local paths
    if dest_lower.startswith("c:\\") or dest_lower.startswith("/home") or dest_lower.startswith("d:\\"):
        return "LOCAL_TRUSTED"

    return "UNKNOWN"


def _infer_device_trust(device_id: str | None, db: Session) -> str:
    """Infer device trust from the device registry."""
    if not device_id:
        return "UNKNOWN"

    from app.models.device import Device
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        return "UNKNOWN"
    if not device.is_active:
        return "UNTRUSTED"
    # Active registered devices are considered managed
    return "MANAGED"


def _infer_user_role(user_context: str | None) -> str:
    """Infer user role from the user_context string on the event."""
    if not user_context:
        return "UNKNOWN"

    upper = user_context.upper()
    if "ADMIN" in upper:
        return "ADMIN"
    if "CONTRACTOR" in upper:
        return "CONTRACTOR"
    if "GUEST" in upper:
        return "GUEST"
    return "EMPLOYEE"


def _count_recent_sensitive_ops(
    db: Session, device_id: str, before: datetime, window_seconds: int = 300
) -> int:
    """Count recent security events from the same device within a time window."""
    cutoff = before - timedelta(seconds=window_seconds)
    return (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.device_id == device_id,
            SecurityEvent.timestamp >= cutoff,
            SecurityEvent.timestamp <= before,
            SecurityEvent.sensitivity_level.isnot(None),
            SecurityEvent.sensitivity_level != "PUBLIC",
        )
        .count()
    )


def build_risk_context_from_event(
    event: SecurityEvent,
    classification: Classification | None,
    db: Session,
) -> RiskContext:
    """Build a complete RiskContext from Phase 2 event + Phase 3 classification."""
    # Sensitivity
    sens_level = "UNKNOWN"
    categories: list[str] = []
    confidence = 0.0
    classifier_version = None

    if classification:
        sens_level = classification.sensitivity_level or "UNKNOWN"
        if classification.categories_json:
            try:
                categories = json.loads(classification.categories_json)
            except (json.JSONDecodeError, TypeError):
                categories = []
        confidence = classification.confidence or 0.0
        classifier_version = classification.classifier_version
    elif event.sensitivity_level:
        sens_level = event.sensitivity_level

    # Action
    action_type = _map_event_type_to_action(event.event_type, event.action)

    # Destination
    destination_type = _infer_destination_type(event.destination, event.event_type)

    # Device trust
    device_trust = _infer_device_trust(event.device_id, db)

    # User role
    user_role = _infer_user_role(event.user_context)

    # Behavioral — count recent sensitive operations
    recent_sensitive_ops = _count_recent_sensitive_ops(
        db, event.device_id, event.timestamp
    )

    return RiskContext(
        event_id=event.event_id,
        sensitivity_level=sens_level,
        sensitivity_categories=categories,
        classification_confidence=confidence,
        classifier_version=classifier_version,
        action_type=action_type,
        event_type=event.event_type,
        destination_type=destination_type,
        destination_identifier=event.destination,
        user_id=event.user_context,
        user_role=user_role,
        device_id=event.device_id,
        device_trust=device_trust,
        recent_sensitive_ops=recent_sensitive_ops,
        recent_total_ops=recent_sensitive_ops,
        rapid_operations=recent_sensitive_ops >= 10,
        unusual_destination=destination_type in ("USB_UNTRUSTED", "EXTERNAL_NETWORK", "PUBLIC_CLOUD"),
        multiple_sensitive_files=recent_sensitive_ops >= 5,
        timestamp=event.timestamp,
        file_size_bytes=event.file_size or 0,
        total_bytes_in_window=event.file_size or 0,
        sensitive_files_in_window=recent_sensitive_ops,
        file_name=event.file_name,
        file_hash=event.file_hash,
        process_name=event.process_name,
        process_id=event.process_id,
    )


def build_risk_context_from_schema(ctx_in: RiskContextInput) -> RiskContext:
    """Build a RiskContext from the API input schema (for simulation)."""
    return RiskContext(
        event_id=ctx_in.event_id,
        sensitivity_level=ctx_in.sensitivity.level,
        sensitivity_categories=ctx_in.sensitivity.categories,
        classification_confidence=ctx_in.sensitivity.confidence,
        classifier_version=ctx_in.sensitivity.classifier_version,
        action_type=ctx_in.action.action_type,
        event_type=ctx_in.action.event_type,
        destination_type=ctx_in.destination.destination_type,
        destination_identifier=ctx_in.destination.destination_identifier,
        user_id=ctx_in.user_context.user_id,
        user_role=ctx_in.user_context.user_role,
        device_id=ctx_in.device_context.device_id,
        device_trust=ctx_in.device_context.device_trust,
        recent_sensitive_ops=ctx_in.behavioral_context.recent_sensitive_ops,
        recent_total_ops=ctx_in.behavioral_context.recent_total_ops,
        rapid_operations=ctx_in.behavioral_context.rapid_operations,
        unusual_destination=ctx_in.behavioral_context.unusual_destination,
        multiple_sensitive_files=ctx_in.behavioral_context.multiple_sensitive_files,
        timestamp=ctx_in.time_context.timestamp,
        is_business_hours=ctx_in.time_context.is_business_hours,
        is_weekend=ctx_in.time_context.is_weekend,
        file_size_bytes=ctx_in.volume_context.file_size_bytes,
        total_bytes_in_window=ctx_in.volume_context.total_bytes_in_window,
        sensitive_files_in_window=ctx_in.volume_context.sensitive_files_in_window,
        file_name=ctx_in.file_context.file_name,
        file_hash=ctx_in.file_context.file_hash,
        process_name=ctx_in.process_name,
        process_id=ctx_in.process_id,
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Policy adapter — load DB policies into PolicyRule
# ═════════════════════════════════════════════════════════════════════════════

def _load_active_policies(db: Session) -> list[PolicyRule]:
    """Load all active (enabled, not soft-deleted) policies."""
    db_policies = (
        db.query(Policy)
        .filter(Policy.enabled.is_(True), Policy.is_deleted.is_(False))
        .order_by(desc(Policy.priority))
        .all()
    )

    rules: list[PolicyRule] = []
    for p in db_policies:
        sensitivity_levels = None
        if p.sensitivity_levels:
            try:
                sensitivity_levels = json.loads(p.sensitivity_levels)
            except (json.JSONDecodeError, TypeError):
                pass

        action_types = None
        if p.action_types:
            try:
                action_types = json.loads(p.action_types)
            except (json.JSONDecodeError, TypeError):
                pass

        destination_types = None
        if p.destination_types:
            try:
                destination_types = json.loads(p.destination_types)
            except (json.JSONDecodeError, TypeError):
                pass

        allowed_actions = None
        if p.allowed_actions:
            try:
                allowed_actions = json.loads(p.allowed_actions)
            except (json.JSONDecodeError, TypeError):
                pass

        conditions = None
        if p.conditions:
            try:
                conditions = json.loads(p.conditions)
            except (json.JSONDecodeError, TypeError):
                pass

        rules.append(PolicyRule(
            id=p.id,
            name=p.name,
            enabled=p.enabled,
            priority=p.priority,
            decision=p.decision,
            version=p.version,
            min_risk_score=p.min_risk_score,
            max_risk_score=p.max_risk_score,
            sensitivity_levels=sensitivity_levels,
            action_types=action_types,
            destination_types=destination_types,
            allowed_actions=allowed_actions,
            risk_threshold=p.risk_threshold,
            conditions=conditions,
        ))

    return rules


# ═════════════════════════════════════════════════════════════════════════════
#  Persistence
# ═════════════════════════════════════════════════════════════════════════════

def _persist_assessment(
    db: Session,
    event_id: str,
    assessment: RiskAssessmentOutput,
    decision: PolicyDecision,
) -> RiskAssessment:
    """Persist a risk assessment to the database."""
    factors_json = json.dumps([
        {
            "name": f.name,
            "score": f.score,
            "weight": f.weight,
            "contribution": f.contribution,
            "reason": f.reason,
        }
        for f in assessment.factors
    ])

    db_assessment = RiskAssessment(
        event_id=event_id,
        risk_engine_version=assessment.engine_version,
        policy_engine_version=_get_policy_engine().version,
        risk_config_version=assessment.config_version,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        decision=decision.decision,
        policy_id=decision.policy_id,
        policy_name=decision.policy_name,
        policy_version=decision.policy_version,
        factor_breakdown_json=factors_json,
        explanation=decision.explanation,
    )
    db.add(db_assessment)
    db.flush()  # get ID
    return db_assessment


def _create_hold_approval(
    db: Session,
    event: SecurityEvent,
    assessment_record: RiskAssessment,
    decision: PolicyDecision,
    system_user_id: int,
) -> ApprovalRequest:
    """Create a PENDING approval request when the decision is HOLD."""
    approval = ApprovalRequest(
        request_id=str(uuid4()),
        event_id=event.id,
        requested_by=system_user_id,
        status=ApprovalStatus.PENDING,
        reason=decision.explanation,
        risk_assessment_id=assessment_record.id,
        requested_action=event.action or event.event_type,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        policy_id=decision.policy_id,
        policy_version=decision.policy_version,
    )
    db.add(approval)
    return approval


# ═════════════════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════════════════

def evaluate_event(
    db: Session,
    event_id: str,
    classification_id: int | None = None,
    actor_user_id: int | None = None,
) -> RiskAssessmentResponse:
    """Full risk evaluation pipeline for an existing event.

    1. Load event + classification from DB
    2. Build RiskContext
    3. Run risk engine
    4. Load policies, run policy engine
    5. Persist assessment
    6. If HOLD → create approval request
    7. Log audit
    8. Return structured response
    """
    risk_engine = _get_risk_engine()
    policy_engine = _get_policy_engine()

    # Load event
    event = db.query(SecurityEvent).filter(SecurityEvent.event_id == event_id).first()
    if not event:
        raise NotFoundError(f"Event not found: {event_id}")

    # Load classification
    classification = None
    if classification_id:
        classification = db.query(Classification).filter(Classification.id == classification_id).first()
    if classification is None:
        classification = (
            db.query(Classification)
            .filter(Classification.event_id == event_id)
            .first()
        )

    # Build context
    context = build_risk_context_from_event(event, classification, db)

    # Risk assessment
    assessment = risk_engine.assess(context)

    # Policy evaluation
    policies = _load_active_policies(db)
    decision = policy_engine.evaluate(context, assessment, policies)

    # Update event with risk score and decision
    event.risk_score = assessment.risk_score
    event.decision = decision.decision
    event.sensitivity_level = context.sensitivity_level

    # Persist assessment
    db_assessment = _persist_assessment(db, event_id, assessment, decision)

    # HOLD → create approval
    if decision.decision == "HOLD":
        # Use the actor_user_id (or the first admin) as the system user
        system_user_id = actor_user_id or 1
        _create_hold_approval(db, event, db_assessment, decision, system_user_id)

    db.commit()
    db.refresh(db_assessment)

    # Audit
    log_action(
        db,
        action=AuditAction.RISK_ASSESSMENT_CREATED,
        actor_user_id=actor_user_id,
        resource_type="RiskAssessment",
        resource_id=str(db_assessment.id),
        metadata={
            "event_id": event_id,
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "decision": decision.decision,
        },
    )

    # Build response
    factors = [
        RiskFactor(
            name=f.name,
            score=f.score,
            weight=f.weight,
            contribution=f.contribution,
            reason=f.reason,
        )
        for f in assessment.factors
    ]

    return RiskAssessmentResponse(
        id=db_assessment.id,
        risk_assessment_id=db_assessment.id,
        event_id=event_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        decision=decision.decision,
        policy_id=decision.policy_id,
        policy_name=decision.policy_name,
        factors=factors,
        explanation=decision.explanation,
        risk_engine_version=assessment.engine_version,
        policy_engine_version=policy_engine.version,
        risk_config_version=assessment.config_version,
        created_at=db_assessment.created_at,
    )


def simulate_policy(
    db: Session,
    context_input: RiskContextInput,
    actor_user_id: int | None = None,
) -> dict[str, Any]:
    """Simulate a policy evaluation without persisting anything."""
    risk_engine = _get_risk_engine()
    policy_engine = _get_policy_engine()

    context = build_risk_context_from_schema(context_input)
    assessment = risk_engine.assess(context)
    policies = _load_active_policies(db)
    decision = policy_engine.evaluate(context, assessment, policies)

    # Audit simulation
    log_action(
        db,
        action=AuditAction.POLICY_SIMULATION_RUN,
        actor_user_id=actor_user_id,
        resource_type="PolicySimulation",
        metadata={
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "decision": decision.decision,
        },
    )

    factors = [
        {
            "name": f.name,
            "score": f.score,
            "weight": f.weight,
            "contribution": f.contribution,
            "reason": f.reason,
        }
        for f in assessment.factors
    ]

    return {
        "risk_score": assessment.risk_score,
        "risk_level": assessment.risk_level,
        "decision": decision.decision,
        "policy_id": decision.policy_id,
        "policy_name": decision.policy_name,
        "factors": factors,
        "matching_policies": decision.matching_policies,
        "explanation": decision.explanation,
    }


def get_risk_assessment(db: Session, assessment_id: int) -> RiskAssessment:
    """Load a single risk assessment by ID."""
    record = db.query(RiskAssessment).filter(RiskAssessment.id == assessment_id).first()
    if not record:
        raise NotFoundError(f"Risk assessment not found: {assessment_id}")
    return record


def list_risk_assessments(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    event_id: str | None = None,
    risk_level: str | None = None,
    decision: str | None = None,
) -> tuple[list[RiskAssessment], int]:
    """List risk assessments with optional filtering."""
    query = db.query(RiskAssessment)
    if event_id:
        query = query.filter(RiskAssessment.event_id == event_id)
    if risk_level:
        query = query.filter(RiskAssessment.risk_level == risk_level)
    if decision:
        query = query.filter(RiskAssessment.decision == decision)
    total = query.count()
    records = query.order_by(desc(RiskAssessment.created_at)).offset(skip).limit(limit).all()
    return records, total
