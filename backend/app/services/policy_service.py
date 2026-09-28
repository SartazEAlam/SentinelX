"""Policy management service — enhanced for Phase 4.

Phase 4 changes:
  - Version incremented on every update
  - Soft-delete: policies referenced by historical assessments are not hard-deleted
  - Enable/disable endpoints with audit logging
  - updated_by tracking
"""

import json

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.policy import Policy
from app.schemas.policies import PolicyCreate, PolicyUpdate
from app.services.audit_service import log_action


def get_policy(db: Session, policy_id: int) -> Policy:
    """Get a policy by ID (excludes soft-deleted)."""
    policy = (
        db.query(Policy)
        .filter(Policy.id == policy_id, Policy.is_deleted.is_(False))
        .first()
    )
    if not policy:
        raise NotFoundError("Policy not found")
    return policy


def list_policies(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = False,
) -> tuple[list[Policy], int]:
    """List policies with pagination (excludes soft-deleted by default)."""
    query = db.query(Policy)
    if not include_deleted:
        query = query.filter(Policy.is_deleted.is_(False))
    total = query.count()
    policies = query.order_by(desc(Policy.priority)).offset(skip).limit(limit).all()
    return policies, total


def create_policy(db: Session, policy_in: PolicyCreate, creator_id: int) -> Policy:
    """Create a new policy."""
    if db.query(Policy).filter(Policy.name == policy_in.name, Policy.is_deleted.is_(False)).first():
        raise ConflictError("Policy with this name already exists")

    policy = Policy(
        name=policy_in.name,
        description=policy_in.description,
        enabled=policy_in.enabled,
        priority=policy_in.priority,
        sensitivity_levels=(
            json.dumps(policy_in.sensitivity_levels) if policy_in.sensitivity_levels else None
        ),
        risk_threshold=policy_in.risk_threshold,
        allowed_actions=(
            json.dumps(policy_in.allowed_actions) if policy_in.allowed_actions else None
        ),
        decision=policy_in.decision,
        conditions=(json.dumps(policy_in.conditions) if policy_in.conditions else None),
        min_risk_score=policy_in.min_risk_score,
        max_risk_score=policy_in.max_risk_score,
        action_types=(json.dumps(policy_in.action_types) if policy_in.action_types else None),
        destination_types=(
            json.dumps(policy_in.destination_types) if policy_in.destination_types else None
        ),
        version=1,
        is_deleted=False,
        created_by=creator_id,
        updated_by=creator_id,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    log_action(
        db,
        action=AuditAction.POLICY_CREATED,
        actor_user_id=creator_id,
        resource_type="Policy",
        resource_id=str(policy.id),
        metadata={"name": policy.name, "version": policy.version},
    )

    return policy


def update_policy(db: Session, policy_id: int, policy_in: PolicyUpdate, actor_id: int) -> Policy:
    """Update an existing policy — increments version."""
    policy = get_policy(db, policy_id)

    if policy_in.name is not None and policy_in.name != policy.name:
        existing = (
            db.query(Policy)
            .filter(Policy.name == policy_in.name, Policy.is_deleted.is_(False))
            .first()
        )
        if existing and existing.id != policy_id:
            raise ConflictError("Policy with this name already exists")
        policy.name = policy_in.name

    if policy_in.description is not None:
        policy.description = policy_in.description
    if policy_in.enabled is not None:
        policy.enabled = policy_in.enabled
    if policy_in.priority is not None:
        policy.priority = policy_in.priority
    if policy_in.sensitivity_levels is not None:
        policy.sensitivity_levels = json.dumps(policy_in.sensitivity_levels)
    if policy_in.risk_threshold is not None:
        policy.risk_threshold = policy_in.risk_threshold
    if policy_in.allowed_actions is not None:
        policy.allowed_actions = json.dumps(policy_in.allowed_actions)
    if policy_in.decision is not None:
        policy.decision = policy_in.decision
    if policy_in.conditions is not None:
        policy.conditions = json.dumps(policy_in.conditions)
    if policy_in.min_risk_score is not None:
        policy.min_risk_score = policy_in.min_risk_score
    if policy_in.max_risk_score is not None:
        policy.max_risk_score = policy_in.max_risk_score
    if policy_in.action_types is not None:
        policy.action_types = json.dumps(policy_in.action_types)
    if policy_in.destination_types is not None:
        policy.destination_types = json.dumps(policy_in.destination_types)

    policy.version += 1
    policy.updated_by = actor_id

    db.commit()
    db.refresh(policy)

    log_action(
        db,
        action=AuditAction.POLICY_UPDATED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy.id),
        metadata={"name": policy.name, "version": policy.version},
    )

    return policy


def delete_policy(db: Session, policy_id: int, actor_id: int) -> None:
    """Soft-delete a policy (preserves reference for historical assessments)."""
    policy = get_policy(db, policy_id)
    policy.is_deleted = True
    policy.enabled = False
    policy.updated_by = actor_id
    policy.version += 1

    db.commit()

    log_action(
        db,
        action=AuditAction.POLICY_DELETED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy_id),
        metadata={"name": policy.name},
    )


def enable_policy(db: Session, policy_id: int, actor_id: int) -> Policy:
    """Enable a policy."""
    policy = get_policy(db, policy_id)
    policy.enabled = True
    policy.updated_by = actor_id
    db.commit()
    db.refresh(policy)

    log_action(
        db,
        action=AuditAction.POLICY_ENABLED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy.id),
    )
    return policy


def disable_policy(db: Session, policy_id: int, actor_id: int) -> Policy:
    """Disable a policy."""
    policy = get_policy(db, policy_id)
    policy.enabled = False
    policy.updated_by = actor_id
    db.commit()
    db.refresh(policy)

    log_action(
        db,
        action=AuditAction.POLICY_DISABLED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy.id),
    )
    return policy
