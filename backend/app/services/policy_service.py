"""Policy management service."""

import json

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.enums import AuditAction
from app.models.policy import Policy
from app.schemas.policies import PolicyCreate, PolicyUpdate
from app.services.audit_service import log_action


def get_policy(db: Session, policy_id: int) -> Policy:
    """Get a policy by ID."""
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise NotFoundError("Policy not found")
    return policy


def list_policies(db: Session, skip: int = 0, limit: int = 50) -> tuple[list[Policy], int]:
    """List policies with pagination."""
    query = db.query(Policy)
    total = query.count()
    policies = query.order_by(desc(Policy.priority)).offset(skip).limit(limit).all()
    
    # Parse JSON fields for API representation
    for p in policies:
        p.sensitivity_levels = json.loads(p.sensitivity_levels) if p.sensitivity_levels else None
        p.allowed_actions = json.loads(p.allowed_actions) if p.allowed_actions else None
        p.conditions = json.loads(p.conditions) if p.conditions else None
        
    return policies, total


def create_policy(db: Session, policy_in: PolicyCreate, creator_id: int) -> Policy:
    """Create a new policy."""
    if db.query(Policy).filter(Policy.name == policy_in.name).first():
        raise ConflictError("Policy with this name already exists")

    policy = Policy(
        name=policy_in.name,
        description=policy_in.description,
        enabled=policy_in.enabled,
        priority=policy_in.priority,
        sensitivity_levels=json.dumps(policy_in.sensitivity_levels) if policy_in.sensitivity_levels else None,
        risk_threshold=policy_in.risk_threshold,
        allowed_actions=json.dumps(policy_in.allowed_actions) if policy_in.allowed_actions else None,
        decision=policy_in.decision,
        conditions=json.dumps(policy_in.conditions) if policy_in.conditions else None,
        created_by=creator_id,
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
        metadata={"name": policy.name},
    )
    
    # Parse JSON back for the response schema
    policy.sensitivity_levels = json.loads(policy.sensitivity_levels) if policy.sensitivity_levels else None
    policy.allowed_actions = json.loads(policy.allowed_actions) if policy.allowed_actions else None
    policy.conditions = json.loads(policy.conditions) if policy.conditions else None

    return policy


def update_policy(db: Session, policy_id: int, policy_in: PolicyUpdate, actor_id: int) -> Policy:
    """Update an existing policy."""
    policy = get_policy(db, policy_id)

    if policy_in.name is not None and policy_in.name != policy.name:
        if db.query(Policy).filter(Policy.name == policy_in.name).first():
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

    db.commit()
    db.refresh(policy)

    log_action(
        db,
        action=AuditAction.POLICY_UPDATED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy.id),
    )
    
    # Parse JSON back for the response schema
    policy.sensitivity_levels = json.loads(policy.sensitivity_levels) if policy.sensitivity_levels else None
    policy.allowed_actions = json.loads(policy.allowed_actions) if policy.allowed_actions else None
    policy.conditions = json.loads(policy.conditions) if policy.conditions else None

    return policy


def delete_policy(db: Session, policy_id: int, actor_id: int) -> None:
    """Delete a policy."""
    policy = get_policy(db, policy_id)
    
    db.delete(policy)
    db.commit()

    log_action(
        db,
        action=AuditAction.POLICY_DELETED,
        actor_user_id=actor_id,
        resource_type="Policy",
        resource_id=str(policy_id),
        metadata={"name": policy.name},
    )
