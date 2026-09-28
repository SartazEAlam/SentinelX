"""Policy engine configuration — default policies and engine versioning.

The policy engine is separate from the risk engine.  The risk engine answers
"how risky is this operation?" while the policy engine answers "what should
SentinelX do about it?"

Default policies are seeded from this module when the database is empty.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.risk_policy_config.risk_config import RiskLevel

# ── Version ──────────────────────────────────────────────────────────────────
POLICY_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class DefaultPolicyRule:
    """A single default policy rule that maps risk level to a decision."""
    name: str
    description: str
    risk_level: str
    decision: str          # ALLOW | HOLD | BLOCK
    priority: int          # Higher = evaluated first
    min_risk_score: int
    max_risk_score: int


@dataclass
class PolicyConfig:
    """Complete policy engine configuration."""

    engine_version: str = POLICY_ENGINE_VERSION

    # Default risk-based policies (seeded if DB is empty)
    default_policies: list[DefaultPolicyRule] = field(default_factory=lambda: [
        DefaultPolicyRule(
            name="Default Low-Risk Allow",
            description="Allow operations with low risk scores (0–29).",
            risk_level=RiskLevel.LOW,
            decision="ALLOW",
            priority=10,
            min_risk_score=0,
            max_risk_score=29,
        ),
        DefaultPolicyRule(
            name="Default Medium-Risk Hold",
            description=(
                "Hold operations with medium risk scores (30–69) "
                "for administrator approval."
            ),
            risk_level=RiskLevel.MEDIUM,
            decision="HOLD",
            priority=10,
            min_risk_score=30,
            max_risk_score=69,
        ),
        DefaultPolicyRule(
            name="Default High-Risk Block",
            description="Block operations with high risk scores (70–100).",
            risk_level=RiskLevel.HIGH,
            decision="BLOCK",
            priority=10,
            min_risk_score=70,
            max_risk_score=100,
        ),
    ])

    def validate(self) -> list[str]:
        """Return a list of configuration errors (empty = valid)."""
        errors: list[str] = []
        valid_decisions = {"ALLOW", "HOLD", "BLOCK"}
        for rule in self.default_policies:
            if rule.decision not in valid_decisions:
                errors.append(
                    f"Policy '{rule.name}' has invalid decision '{rule.decision}'"
                )
            if not (0 <= rule.min_risk_score <= rule.max_risk_score <= 100):
                errors.append(
                    f"Policy '{rule.name}' has invalid risk score range: "
                    f"{rule.min_risk_score}–{rule.max_risk_score}"
                )
            if rule.priority < 1:
                errors.append(
                    f"Policy '{rule.name}' has invalid priority {rule.priority}"
                )
        return errors


def get_default_policy_config() -> PolicyConfig:
    """Return the default policy configuration, validated."""
    cfg = PolicyConfig()
    errors = cfg.validate()
    if errors:
        raise ValueError(f"Default policy configuration is invalid: {errors}")
    return cfg
