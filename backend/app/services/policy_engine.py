"""Policy engine — determines the enforcement decision for a risk assessment.

Separation of concerns:
  * Risk engine → "How risky is this operation?"
  * Policy engine → "What should SentinelX do about it?"

The policy engine evaluates all enabled policies in priority order and returns
the first match.  If no custom policy matches, the default risk-level-based
policy is applied.

The engine is testable without FastAPI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.risk_policy_config.policy_config import (
    POLICY_ENGINE_VERSION,
    PolicyConfig,
    get_default_policy_config,
)
from app.services.risk_engine import RiskAssessmentOutput, RiskContext

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  Output dataclass
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class PolicyDecision:
    """The result of evaluating policies against a risk assessment."""
    decision: str              # ALLOW | HOLD | BLOCK
    policy_id: int | None = None
    policy_name: str | None = None
    policy_version: int | None = None
    explanation: str = ""
    matching_policies: list[dict[str, Any]] = field(default_factory=list)


# ═════════════════════════════════════════════════════════════════════════════
#  Policy representation (lightweight, in-memory)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class PolicyRule:
    """An in-memory representation of a policy used for evaluation.

    This is distinct from the SQLAlchemy ORM model to keep the engine
    independent of the database layer.
    """
    id: int
    name: str
    enabled: bool
    priority: int
    decision: str | None            # ALLOW | HOLD | BLOCK
    version: int = 1

    # Conditions (all optional; a condition not set means "any")
    min_risk_score: float | None = None
    max_risk_score: float | None = None
    sensitivity_levels: list[str] | None = None
    action_types: list[str] | None = None
    destination_types: list[str] | None = None
    allowed_actions: list[str] | None = None
    risk_threshold: float | None = None
    conditions: dict[str, Any] | None = None


# ═════════════════════════════════════════════════════════════════════════════
#  Policy Engine
# ═════════════════════════════════════════════════════════════════════════════

class PolicyEngine:
    """Configurable, deterministic policy evaluation engine.

    Usage::

        engine = PolicyEngine()
        decision = engine.evaluate(context, risk_assessment, policies)
    """

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self._config = config or get_default_policy_config()
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Policy configuration is invalid: {errors}")

    @property
    def version(self) -> str:
        return POLICY_ENGINE_VERSION

    def evaluate(
        self,
        context: RiskContext,
        assessment: RiskAssessmentOutput,
        policies: list[PolicyRule] | None = None,
    ) -> PolicyDecision:
        """Evaluate policies against a risk assessment.

        Precedence rules:
          1. Disabled policies are ignored.
          2. Policies are evaluated by priority (highest first).
          3. Among matching policies, highest priority wins.
          4. If no custom policy matches, the default risk-level policy applies.
          5. Invalid policies are logged and skipped (fail-safe).

        Returns a deterministic ``PolicyDecision``.
        """
        matching: list[dict[str, Any]] = []

        if policies:
            # Sort by priority descending (highest priority first)
            sorted_policies = sorted(
                [p for p in policies if p.enabled],
                key=lambda p: p.priority,
                reverse=True,
            )

            for policy in sorted_policies:
                try:
                    if self._matches(policy, context, assessment):
                        match_info = {
                            "id": policy.id,
                            "name": policy.name,
                            "priority": policy.priority,
                            "decision": policy.decision,
                            "version": policy.version,
                        }
                        matching.append(match_info)
                except Exception:
                    logger.exception(
                        "Error evaluating policy %d (%s) — skipping",
                        policy.id, policy.name,
                    )
                    continue

        # Select the highest-priority match
        if matching:
            winner = matching[0]
            decision_str = winner.get("decision", "").upper()
            if decision_str not in ("ALLOW", "HOLD", "BLOCK"):
                logger.warning(
                    "Policy %s has invalid decision '%s' — using default",
                    winner.get("name"), decision_str,
                )
            else:
                return PolicyDecision(
                    decision=decision_str,
                    policy_id=winner.get("id"),
                    policy_name=winner.get("name"),
                    policy_version=winner.get("version"),
                    explanation=self._build_explanation(
                        decision_str, winner, assessment, context
                    ),
                    matching_policies=matching,
                )

        # ── Default risk-level-based policy ──────────────────────────────
        return self._apply_default_policy(assessment, context)

    # ── Condition matching ───────────────────────────────────────────────

    def _matches(
        self,
        policy: PolicyRule,
        context: RiskContext,
        assessment: RiskAssessmentOutput,
    ) -> bool:
        """Check whether a policy's conditions match the current context/assessment."""

        # Risk score range
        if policy.min_risk_score is not None:
            if assessment.risk_score < policy.min_risk_score:
                return False
        if policy.max_risk_score is not None:
            if assessment.risk_score > policy.max_risk_score:
                return False

        # Legacy risk_threshold (from Phase 1: "risk >= threshold → match")
        if policy.risk_threshold is not None:
            if assessment.risk_score < policy.risk_threshold:
                return False

        # Sensitivity levels
        if policy.sensitivity_levels:
            ctx_level = context.sensitivity_level.upper()
            if ctx_level not in [s.upper() for s in policy.sensitivity_levels]:
                return False

        # Action types
        if policy.action_types:
            ctx_action = context.action_type.upper()
            if ctx_action not in [a.upper() for a in policy.action_types]:
                return False

        # Destination types
        if policy.destination_types:
            ctx_dest = context.destination_type.upper()
            if ctx_dest not in [d.upper() for d in policy.destination_types]:
                return False

        # Allowed actions (Phase 1 legacy: if action is in allowed list → no match)
        if policy.allowed_actions:
            ctx_action = context.action_type.upper()
            if ctx_action in [a.upper() for a in policy.allowed_actions]:
                return False  # action is explicitly allowed, so this restrictive policy doesn't apply

        # Extended conditions (JSON dict with AND semantics)
        if policy.conditions:
            if not self._evaluate_conditions(policy.conditions, context, assessment):
                return False

        return True

    def _evaluate_conditions(
        self,
        conditions: dict[str, Any],
        context: RiskContext,
        assessment: RiskAssessmentOutput,
    ) -> bool:
        """Evaluate extended JSON conditions with AND semantics.

        Supported keys:
          - risk_level: str or list[str]
          - min_risk_score, max_risk_score: float
          - sensitivity_level: str or list[str]
          - action_type: str or list[str]
          - destination_type: str or list[str]
          - user_role: str or list[str]
          - device_trust: str or list[str]
        """
        for key, expected in conditions.items():
            key_lower = key.lower()

            if key_lower == "risk_level":
                if not self._match_value(assessment.risk_level, expected):
                    return False

            elif key_lower == "min_risk_score":
                if assessment.risk_score < float(expected):
                    return False

            elif key_lower == "max_risk_score":
                if assessment.risk_score > float(expected):
                    return False

            elif key_lower == "sensitivity_level":
                if not self._match_value(context.sensitivity_level, expected):
                    return False

            elif key_lower == "action_type":
                if not self._match_value(context.action_type, expected):
                    return False

            elif key_lower == "destination_type":
                if not self._match_value(context.destination_type, expected):
                    return False

            elif key_lower == "user_role":
                if not self._match_value(context.user_role, expected):
                    return False

            elif key_lower == "device_trust":
                if not self._match_value(context.device_trust, expected):
                    return False

            # Unknown keys are silently ignored (forward compatibility)

        return True

    @staticmethod
    def _match_value(actual: str, expected: Any) -> bool:
        """Match a string value against a single string or list of strings."""
        actual_upper = actual.upper()
        if isinstance(expected, list):
            return actual_upper in [str(e).upper() for e in expected]
        return actual_upper == str(expected).upper()

    # ── Default policy ───────────────────────────────────────────────────

    def _apply_default_policy(
        self,
        assessment: RiskAssessmentOutput,
        context: RiskContext,
    ) -> PolicyDecision:
        """Apply the built-in default risk-level-based policy."""
        level = assessment.risk_level.upper()

        decision_map = {}
        for rule in self._config.default_policies:
            if rule.min_risk_score <= assessment.risk_score <= rule.max_risk_score:
                decision_map[rule.risk_level] = rule.decision

        decision = decision_map.get(level, "HOLD")

        # Fail-safe: unknown level → HOLD (conservative, not ALLOW)
        if decision not in ("ALLOW", "HOLD", "BLOCK"):
            logger.warning(
                "Default policy produced invalid decision '%s' for level '%s' — using HOLD",
                decision, level,
            )
            decision = "HOLD"

        return PolicyDecision(
            decision=decision,
            policy_id=None,
            policy_name=f"Default {level} Policy",
            policy_version=None,
            explanation=self._build_explanation(decision, None, assessment, context),
            matching_policies=[],
        )

    # ── Explanation ──────────────────────────────────────────────────────

    def _build_explanation(
        self,
        decision: str,
        policy_info: dict[str, Any] | None,
        assessment: RiskAssessmentOutput,
        context: RiskContext,
    ) -> str:
        """Generate a human-readable explanation of the policy decision."""
        parts: list[str] = [f"Decision: {decision}"]

        if policy_info:
            parts.append(
                f"Matched policy: {policy_info.get('name', 'Unknown')} "
                f"(priority={policy_info.get('priority', '?')}, "
                f"version={policy_info.get('version', '?')})"
            )
        else:
            parts.append(f"Applied default risk-level policy for level: {assessment.risk_level}")

        parts.append(f"Risk score: {assessment.risk_score:.1f} ({assessment.risk_level})")

        # Top factors
        sorted_factors = sorted(assessment.factors, key=lambda f: f.contribution, reverse=True)
        top_factors = [f for f in sorted_factors if f.contribution > 0][:3]
        if top_factors:
            parts.append("Primary risk factors:")
            for f in top_factors:
                parts.append(f"  - {f.name}: {f.reason}")

        return "\n".join(parts)
