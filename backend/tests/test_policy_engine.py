"""Phase 4 — Policy Engine unit tests.

Tests the policy engine in isolation (no database, no FastAPI).
"""

import pytest

from app.risk_policy_config.policy_config import get_default_policy_config
from app.services.policy_engine import PolicyDecision, PolicyEngine, PolicyRule
from app.services.risk_engine import RiskAssessmentOutput, RiskContext, RiskFactorResult


@pytest.fixture
def engine() -> PolicyEngine:
    return PolicyEngine()


def _make_assessment(score: float, level: str) -> RiskAssessmentOutput:
    return RiskAssessmentOutput(
        risk_score=score,
        risk_level=level,
        factors=[
            RiskFactorResult(
                name="data_sensitivity", score=score, weight=0.3,
                contribution=score * 0.3, reason="test"
            ),
        ],
        explanation="test",
        engine_version="1.0.0",
        config_version="1.0.0",
    )


def _make_context(**kwargs: object) -> RiskContext:
    return RiskContext(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# Default risk-level policies
# ═══════════════════════════════════════════════════════════════════════════

class TestDefaultPolicy:
    def test_low_risk_allows(self, engine: PolicyEngine) -> None:
        ctx = _make_context(sensitivity_level="PUBLIC")
        assessment = _make_assessment(15.0, "LOW")
        decision = engine.evaluate(ctx, assessment)
        assert decision.decision == "ALLOW"

    def test_medium_risk_holds(self, engine: PolicyEngine) -> None:
        ctx = _make_context(sensitivity_level="CONFIDENTIAL")
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment)
        assert decision.decision == "HOLD"

    def test_high_risk_blocks(self, engine: PolicyEngine) -> None:
        ctx = _make_context(sensitivity_level="HIGHLY_CONFIDENTIAL")
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment)
        assert decision.decision == "BLOCK"


# ═══════════════════════════════════════════════════════════════════════════
# Test 9 — Policy override
# ═══════════════════════════════════════════════════════════════════════════

class TestPolicyOverride:
    def test_custom_policy_overrides_default(self, engine: PolicyEngine) -> None:
        """A high-priority custom ALLOW policy should override the default BLOCK."""
        custom_policy = PolicyRule(
            id=99,
            name="Emergency Override",
            enabled=True,
            priority=200,
            decision="ALLOW",
            min_risk_score=0,
            max_risk_score=100,
            sensitivity_levels=["HIGHLY_CONFIDENTIAL"],
            action_types=["USB_TRANSFER"],
        )
        ctx = _make_context(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            action_type="USB_TRANSFER",
        )
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment, [custom_policy])
        assert decision.decision == "ALLOW"
        assert decision.policy_id == 99
        assert decision.policy_name == "Emergency Override"


# ═══════════════════════════════════════════════════════════════════════════
# Test 10 — Disabled policy
# ═══════════════════════════════════════════════════════════════════════════

class TestDisabledPolicy:
    def test_disabled_policy_ignored(self, engine: PolicyEngine) -> None:
        disabled = PolicyRule(
            id=10, name="Disabled", enabled=False,
            priority=500, decision="ALLOW",
            min_risk_score=0, max_risk_score=100,
        )
        ctx = _make_context()
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment, [disabled])
        # Should fall through to default BLOCK
        assert decision.decision == "BLOCK"


# ═══════════════════════════════════════════════════════════════════════════
# Test 11 — Policy conflict (deterministic selection)
# ═══════════════════════════════════════════════════════════════════════════

class TestPolicyConflict:
    def test_highest_priority_wins(self, engine: PolicyEngine) -> None:
        low_prio = PolicyRule(
            id=1, name="Low Priority", enabled=True,
            priority=10, decision="ALLOW",
            min_risk_score=0, max_risk_score=100,
        )
        high_prio = PolicyRule(
            id=2, name="High Priority", enabled=True,
            priority=100, decision="BLOCK",
            min_risk_score=0, max_risk_score=100,
        )
        ctx = _make_context()
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [low_prio, high_prio])
        assert decision.decision == "BLOCK"
        assert decision.policy_id == 2

    def test_deterministic_across_runs(self, engine: PolicyEngine) -> None:
        policies = [
            PolicyRule(id=1, name="A", enabled=True, priority=50, decision="HOLD",
                       min_risk_score=0, max_risk_score=100),
            PolicyRule(id=2, name="B", enabled=True, priority=50, decision="BLOCK",
                       min_risk_score=0, max_risk_score=100),
        ]
        ctx = _make_context()
        assessment = _make_assessment(60.0, "MEDIUM")
        d1 = engine.evaluate(ctx, assessment, policies)
        d2 = engine.evaluate(ctx, assessment, policies)
        assert d1.decision == d2.decision
        assert d1.policy_id == d2.policy_id


# ═══════════════════════════════════════════════════════════════════════════
# Test 12 — Invalid policy
# ═══════════════════════════════════════════════════════════════════════════

class TestInvalidPolicy:
    def test_invalid_decision_falls_through(self, engine: PolicyEngine) -> None:
        bad_policy = PolicyRule(
            id=5, name="Bad Decision", enabled=True,
            priority=999, decision="INVALID_DECISION",
            min_risk_score=0, max_risk_score=100,
        )
        ctx = _make_context()
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment, [bad_policy])
        # Should fall through to default since decision is invalid
        assert decision.decision == "BLOCK"


# ═══════════════════════════════════════════════════════════════════════════
# Policy condition matching
# ═══════════════════════════════════════════════════════════════════════════

class TestConditionMatching:
    def test_sensitivity_filter(self, engine: PolicyEngine) -> None:
        """Policy only matches HIGHLY_CONFIDENTIAL — should not match INTERNAL."""
        policy = PolicyRule(
            id=1, name="HC Only", enabled=True,
            priority=100, decision="BLOCK",
            sensitivity_levels=["HIGHLY_CONFIDENTIAL"],
        )
        ctx = _make_context(sensitivity_level="INTERNAL")
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [policy])
        # Should NOT match — falls through to default HOLD
        assert decision.decision == "HOLD"

    def test_action_type_filter(self, engine: PolicyEngine) -> None:
        policy = PolicyRule(
            id=1, name="USB Block", enabled=True,
            priority=100, decision="BLOCK",
            action_types=["USB_TRANSFER"],
        )
        ctx = _make_context(action_type="COPY")
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [policy])
        assert decision.decision == "HOLD"  # no match

    def test_destination_type_filter(self, engine: PolicyEngine) -> None:
        policy = PolicyRule(
            id=1, name="Cloud Block", enabled=True,
            priority=100, decision="BLOCK",
            destination_types=["PUBLIC_CLOUD"],
        )
        ctx = _make_context(destination_type="LOCAL_TRUSTED")
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [policy])
        assert decision.decision == "HOLD"  # no match

    def test_risk_score_range(self, engine: PolicyEngine) -> None:
        policy = PolicyRule(
            id=1, name="Medium Range", enabled=True,
            priority=100, decision="HOLD",
            min_risk_score=30, max_risk_score=69,
        )
        ctx = _make_context()
        assessment_low = _make_assessment(15.0, "LOW")
        decision_low = engine.evaluate(ctx, assessment_low, [policy])
        assert decision_low.decision == "ALLOW"  # no match, default LOW

        assessment_mid = _make_assessment(50.0, "MEDIUM")
        decision_mid = engine.evaluate(ctx, assessment_mid, [policy])
        assert decision_mid.decision == "HOLD"  # matches

    def test_json_conditions(self, engine: PolicyEngine) -> None:
        policy = PolicyRule(
            id=1, name="Conditional", enabled=True,
            priority=100, decision="BLOCK",
            conditions={
                "sensitivity_level": "HIGHLY_CONFIDENTIAL",
                "action_type": "USB_TRANSFER",
                "destination_type": "USB_UNTRUSTED",
            },
        )
        ctx_match = _make_context(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            action_type="USB_TRANSFER",
            destination_type="USB_UNTRUSTED",
        )
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx_match, assessment, [policy])
        assert decision.decision == "BLOCK"
        assert decision.policy_id == 1

    def test_json_conditions_no_match(self, engine: PolicyEngine) -> None:
        policy = PolicyRule(
            id=1, name="Conditional", enabled=True,
            priority=100, decision="BLOCK",
            conditions={
                "sensitivity_level": "HIGHLY_CONFIDENTIAL",
                "destination_type": "USB_UNTRUSTED",
            },
        )
        ctx = _make_context(
            sensitivity_level="INTERNAL",
            destination_type="USB_UNTRUSTED",
        )
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [policy])
        assert decision.decision == "HOLD"  # falls through

    def test_approved_cloud_internal_allow(self, engine: PolicyEngine) -> None:
        """IF destination=APPROVED_CLOUD AND sensitivity<=INTERNAL THEN ALLOW."""
        policy = PolicyRule(
            id=1, name="Cloud Allow", enabled=True,
            priority=100, decision="ALLOW",
            conditions={
                "destination_type": "APPROVED_CLOUD",
                "sensitivity_level": ["PUBLIC", "INTERNAL"],
            },
        )
        ctx = _make_context(
            sensitivity_level="INTERNAL",
            destination_type="APPROVED_CLOUD",
        )
        assessment = _make_assessment(50.0, "MEDIUM")
        decision = engine.evaluate(ctx, assessment, [policy])
        assert decision.decision == "ALLOW"


# ═══════════════════════════════════════════════════════════════════════════
# Explanation
# ═══════════════════════════════════════════════════════════════════════════

class TestPolicyExplanation:
    def test_explanation_contains_decision(self, engine: PolicyEngine) -> None:
        ctx = _make_context()
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment)
        assert "BLOCK" in decision.explanation

    def test_explanation_contains_risk_score(self, engine: PolicyEngine) -> None:
        ctx = _make_context()
        assessment = _make_assessment(85.0, "HIGH")
        decision = engine.evaluate(ctx, assessment)
        assert "85.0" in decision.explanation
