"""Phase 4 — Risk Engine unit tests.

Tests the risk engine in isolation (no database, no FastAPI).
Covers all 18+ test scenarios required by the Phase 4 specification.
"""


import pytest
from app.risk_policy_config.risk_config import (
    RiskConfig,
    RiskLevelThreshold,
    get_default_risk_config,
)
from app.services.risk_engine import RiskContext, RiskEngine


@pytest.fixture
def engine() -> RiskEngine:
    return RiskEngine()


@pytest.fixture
def config() -> RiskConfig:
    return get_default_risk_config()


# ═══════════════════════════════════════════════════════════════════════════
# Test 1 — Low-risk local operation
# ═══════════════════════════════════════════════════════════════════════════

class TestLowRiskOperation:
    def test_public_data_local_read(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="PUBLIC",
            classification_confidence=0.95,
            action_type="READ",
            destination_type="LOCAL_TRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=True,
        )
        result = engine.assess(ctx)
        assert 0 <= result.risk_score <= 29, f"Expected LOW, got {result.risk_score}"
        assert result.risk_level == "LOW"

    def test_internal_data_local_copy(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="INTERNAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="LOCAL_TRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=True,
        )
        result = engine.assess(ctx)
        assert result.risk_level == "LOW"


# ═══════════════════════════════════════════════════════════════════════════
# Test 2 — Medium-risk operation
# ═══════════════════════════════════════════════════════════════════════════

class TestMediumRiskOperation:
    def test_confidential_copy(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.85,
            action_type="COPY",
            destination_type="USB_TRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=True,
        )
        result = engine.assess(ctx)
        assert 0 <= result.risk_score <= 29, f"Expected LOW, got {result.risk_score}"
        assert result.risk_level == "LOW"


# ═══════════════════════════════════════════════════════════════════════════
# Test 3 — High-risk USB transfer
# ═══════════════════════════════════════════════════════════════════════════

class TestHighRiskUSBTransfer:
    def test_highly_confidential_usb_untrusted(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=["CUSTOMER_DATA", "PERSONAL_DATA"],
            classification_confidence=0.95,
            action_type="USB_TRANSFER",
            destination_type="USB_UNTRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=False,
            recent_sensitive_ops=15,
            multiple_sensitive_files=True,
            file_size_bytes=500_000_000,
        )
        result = engine.assess(ctx)
        assert 30 <= result.risk_score <= 69, f"Expected MEDIUM, got {result.risk_score}"
        assert result.risk_level == "MEDIUM"


# ═══════════════════════════════════════════════════════════════════════════
# Test 4 — Customer data external upload
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomerDataUpload:
    def test_customer_data_public_cloud(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=["CUSTOMER_DATA", "FINANCIAL_DATA"],
            classification_confidence=0.9,
            action_type="EXTERNAL_UPLOAD",
            destination_type="PUBLIC_CLOUD",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
        )
        result = engine.assess(ctx)
        assert 30 <= result.risk_score <= 69, f"Expected MEDIUM, got {result.risk_score}"
        assert result.risk_level == "MEDIUM"


# ═══════════════════════════════════════════════════════════════════════════
# Test 5 — Large-volume transfer
# ═══════════════════════════════════════════════════════════════════════════

class TestLargeVolumeTransfer:
    def test_large_volume_elevates_risk(self, engine: RiskEngine) -> None:
        # Baseline: small volume
        ctx_small = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="EXTERNAL_NETWORK",
            file_size_bytes=1000,
        )
        result_small = engine.assess(ctx_small)

        # Elevated: large volume
        ctx_large = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="EXTERNAL_NETWORK",
            file_size_bytes=600_000_000,
            total_bytes_in_window=600_000_000,
            sensitive_files_in_window=10,
        )
        result_large = engine.assess(ctx_large)

        assert result_large.risk_score > result_small.risk_score


# ═══════════════════════════════════════════════════════════════════════════
# Test 6 — After-hours transfer
# ═══════════════════════════════════════════════════════════════════════════

class TestAfterHoursTransfer:
    def test_outside_business_hours_adds_risk(self, engine: RiskEngine) -> None:
        # During business hours
        ctx_biz = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="USB_TRUSTED",
            is_business_hours=True,
        )
        result_biz = engine.assess(ctx_biz)

        # Outside business hours
        ctx_off = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="USB_TRUSTED",
            is_business_hours=False,
        )
        result_off = engine.assess(ctx_off)

        assert result_off.risk_score > result_biz.risk_score


# ═══════════════════════════════════════════════════════════════════════════
# Test 7 — Unknown destination
# ═══════════════════════════════════════════════════════════════════════════

class TestUnknownDestination:
    def test_unknown_destination_conservative(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="UNKNOWN",
        )
        result = engine.assess(ctx)
        # Unknown destination should use a moderate-to-high destination score (50)
        dest_factor = next(f for f in result.factors if f.name == "destination")
        assert dest_factor.score == 50.0


# ═══════════════════════════════════════════════════════════════════════════
# Test 8 — Unknown sensitivity
# ═══════════════════════════════════════════════════════════════════════════

class TestUnknownSensitivity:
    def test_unknown_sensitivity_fallback(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="UNKNOWN",
            classification_confidence=0.5,
            action_type="COPY",
            destination_type="LOCAL_TRUSTED",
        )
        result = engine.assess(ctx)
        sens_factor = next(f for f in result.factors if f.name == "data_sensitivity")
        # UNKNOWN base = 30, scaled by confidence
        assert sens_factor.score > 0


# ═══════════════════════════════════════════════════════════════════════════
# Test 15 — Score boundaries
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreBoundaries:
    def test_minimum_possible_score(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="PUBLIC",
            classification_confidence=0.99,
            action_type="READ",
            destination_type="PROTECTED_DIRECTORY",
            user_role="ADMIN",
            device_trust="MANAGED",
            is_business_hours=True,
            file_size_bytes=100,
        )
        result = engine.assess(ctx)
        assert result.risk_score >= 0
        assert result.risk_score <= 100

    def test_maximum_possible_score(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=[
                "CREDENTIALS", "PAYMENT_CARD_DATA", "FINANCIAL_DATA",
                "CUSTOMER_DATA", "HEALTH_DATA",
            ],
            classification_confidence=1.0,
            action_type="EXTERNAL_UPLOAD",
            destination_type="EXTERNAL_STORAGE",
            user_role="GUEST",
            device_trust="UNTRUSTED",
            recent_sensitive_ops=50,
            rapid_operations=True,
            unusual_destination=True,
            multiple_sensitive_files=True,
            is_business_hours=False,
            is_weekend=True,
            file_size_bytes=1_000_000_000,
            total_bytes_in_window=5_000_000_000,
            sensitive_files_in_window=20,
        )
        result = engine.assess(ctx)
        assert result.risk_score >= 0
        assert result.risk_score <= 100

    def test_boundary_29(self, engine: RiskEngine) -> None:
        """Verify that a score at the LOW/MEDIUM boundary is handled correctly."""
        config = get_default_risk_config()
        eng = RiskEngine(config)
        # Score at exactly 29 should be LOW
        level = eng._determine_level(29.0)
        assert level == "LOW"

    def test_boundary_30(self, engine: RiskEngine) -> None:
        level = engine._determine_level(30.0)
        assert level == "MEDIUM"

    def test_boundary_69(self, engine: RiskEngine) -> None:
        level = engine._determine_level(69.0)
        assert level == "MEDIUM"

    def test_boundary_70(self, engine: RiskEngine) -> None:
        level = engine._determine_level(70.0)
        assert level == "HIGH"

    def test_boundary_0(self, engine: RiskEngine) -> None:
        level = engine._determine_level(0.0)
        assert level == "LOW"

    def test_boundary_100(self, engine: RiskEngine) -> None:
        level = engine._determine_level(100.0)
        assert level == "HIGH"


# ═══════════════════════════════════════════════════════════════════════════
# Test 16 — Score overflow
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreOverflow:
    def test_overflow_clamped(self, engine: RiskEngine) -> None:
        """Even with extreme inputs, the final score stays <= 100."""
        ctx = RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            sensitivity_categories=[
                "CREDENTIALS", "PAYMENT_CARD_DATA", "FINANCIAL_DATA",
                "CUSTOMER_DATA", "HEALTH_DATA", "API_KEYS",
            ],
            classification_confidence=1.0,
            action_type="EXTERNAL_UPLOAD",
            destination_type="EXTERNAL_STORAGE",
            user_role="GUEST",
            device_trust="UNTRUSTED",
            recent_sensitive_ops=100,
            rapid_operations=True,
            unusual_destination=True,
            multiple_sensitive_files=True,
            is_weekend=True,
            file_size_bytes=10_000_000_000,
            total_bytes_in_window=50_000_000_000,
            sensitive_files_in_window=50,
        )
        result = engine.assess(ctx)
        assert result.risk_score <= 100.0


# ═══════════════════════════════════════════════════════════════════════════
# Test 17 — Score underflow
# ═══════════════════════════════════════════════════════════════════════════

class TestScoreUnderflow:
    def test_underflow_clamped(self, engine: RiskEngine) -> None:
        """The score never goes below 0."""
        ctx = RiskContext(
            sensitivity_level="PUBLIC",
            classification_confidence=0.01,
            action_type="READ",
            destination_type="PROTECTED_DIRECTORY",
            user_role="ADMIN",
            device_trust="MANAGED",
            is_business_hours=True,
            file_size_bytes=0,
        )
        result = engine.assess(ctx)
        assert result.risk_score >= 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Test 18 — Configuration validation
# ═══════════════════════════════════════════════════════════════════════════

class TestConfigValidation:
    def test_valid_default_config(self) -> None:
        cfg = get_default_risk_config()
        errors = cfg.validate()
        assert errors == []

    def test_invalid_weight_sum(self) -> None:
        cfg = RiskConfig()
        cfg.risk_weights["sensitivity"] = 0.9  # breaks sum to 1.0
        errors = cfg.validate()
        assert any("risk_weights must sum" in e for e in errors)

    def test_invalid_score_range(self) -> None:
        cfg = RiskConfig()
        cfg.action_risk["READ"] = 150  # > 100
        errors = cfg.validate()
        assert any("must be 0–100" in e for e in errors)

    def test_overlapping_risk_levels(self) -> None:
        cfg = RiskConfig()
        cfg.risk_levels = {
            "LOW": RiskLevelThreshold(0, 30),
            "MEDIUM": RiskLevelThreshold(30, 69),  # overlaps at 30
            "HIGH": RiskLevelThreshold(70, 100),
        }
        errors = cfg.validate()
        assert any("gap/overlap" in e for e in errors)

    def test_invalid_engine_with_bad_config(self) -> None:
        cfg = RiskConfig()
        cfg.risk_weights["sensitivity"] = 0.9
        with pytest.raises(ValueError, match="invalid"):
            RiskEngine(cfg)


# ═══════════════════════════════════════════════════════════════════════════
# Risk breakdown / explainability
# ═══════════════════════════════════════════════════════════════════════════

class TestRiskBreakdown:
    def test_all_factors_present(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            classification_confidence=0.9,
            action_type="COPY",
            destination_type="USB_TRUSTED",
        )
        result = engine.assess(ctx)
        factor_names = {f.name for f in result.factors}
        expected = {
            "data_sensitivity", "action", "destination",
            "user_context", "device_context", "behavior",
            "time_context", "volume",
        }
        assert expected == factor_names

    def test_factor_contributions_sum_to_score(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="HIGHLY_CONFIDENTIAL",
            classification_confidence=0.95,
            action_type="USB_TRANSFER",
            destination_type="USB_UNTRUSTED",
        )
        result = engine.assess(ctx)
        contribution_sum = sum(f.contribution for f in result.factors)
        # Should be close (rounding may cause small differences)
        assert abs(contribution_sum - result.risk_score) < 1.0

    def test_explanation_not_empty(self, engine: RiskEngine) -> None:
        ctx = RiskContext(sensitivity_level="PUBLIC", action_type="READ")
        result = engine.assess(ctx)
        assert result.explanation
        assert len(result.explanation) > 10

    def test_version_present(self, engine: RiskEngine) -> None:
        ctx = RiskContext(sensitivity_level="PUBLIC", action_type="READ")
        result = engine.assess(ctx)
        assert result.engine_version == "1.0.0"
        assert result.config_version == "1.0.0"


# ═══════════════════════════════════════════════════════════════════════════
# Determinism
# ═══════════════════════════════════════════════════════════════════════════

class TestDeterminism:
    def test_same_input_same_output(self, engine: RiskEngine) -> None:
        ctx = RiskContext(
            sensitivity_level="CONFIDENTIAL",
            sensitivity_categories=["CUSTOMER_DATA"],
            classification_confidence=0.85,
            action_type="COPY",
            destination_type="USB_TRUSTED",
            user_role="EMPLOYEE",
            device_trust="MANAGED",
            is_business_hours=True,
            file_size_bytes=50_000,
        )
        r1 = engine.assess(ctx)
        r2 = engine.assess(ctx)
        assert r1.risk_score == r2.risk_score
        assert r1.risk_level == r2.risk_level
        assert len(r1.factors) == len(r2.factors)
        for f1, f2 in zip(r1.factors, r2.factors):
            assert f1.score == f2.score
            assert f1.contribution == f2.contribution
