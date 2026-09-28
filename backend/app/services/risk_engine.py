"""Risk engine — the central risk-scoring service.

The risk engine:
  1. Accepts a ``RiskContext`` (dataclass, NOT a Pydantic schema)
  2. Calculates per-component scores using risk_factors
  3. Applies configurable weights
  4. Produces a final score (0–100), risk level, and explainable breakdown

The engine is testable without FastAPI or a database.

Risk Score Formula
══════════════════

  final_score = clamp(Σ (component_score_i × weight_i), 0, 100)

Where each component_score_i is a normalized value in [0, 100] and weight_i
is the configurable weight for that component (all weights sum to 1.0).

Components:
  1. sensitivity  — from Phase 3 classification (level + categories)
  2. action       — the type of file/data operation
  3. destination  — where the data is going
  4. user_context — role-based risk contribution
  5. device_context — device trust level
  6. behavior     — frequency, volume patterns, anomalies
  7. time_context — business hours vs. off-hours
  8. volume       — transfer size and aggregation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.risk_policy_config.risk_config import RISK_ENGINE_VERSION, RiskConfig, RiskLevel, get_default_risk_config
from app.services.risk_factors import (
    calculate_action_score,
    calculate_behavior_score,
    calculate_destination_score,
    calculate_device_context_score,
    calculate_sensitivity_score,
    calculate_time_context_score,
    calculate_user_context_score,
    calculate_volume_score,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
#  Input context (framework-agnostic dataclass)
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class RiskContext:
    """All inputs needed for a risk assessment.

    This is a plain dataclass so the engine can be used without Pydantic or
    FastAPI.
    """
    # Sensitivity
    sensitivity_level: str = "UNKNOWN"
    sensitivity_categories: list[str] = field(default_factory=list)
    classification_confidence: float = 0.0
    classifier_version: str | None = None

    # Action
    action_type: str = "UNKNOWN"
    event_type: str | None = None

    # Destination
    destination_type: str = "UNKNOWN"
    destination_identifier: str | None = None

    # User
    user_id: str | None = None
    user_role: str = "UNKNOWN"

    # Device
    device_id: str | None = None
    device_trust: str = "UNKNOWN"

    # Behavioral
    recent_sensitive_ops: int = 0
    recent_total_ops: int = 0
    rapid_operations: bool = False
    unusual_destination: bool = False
    multiple_sensitive_files: bool = False

    # Time
    timestamp: datetime | None = None
    is_business_hours: bool | None = None
    is_weekend: bool | None = None

    # Volume
    file_size_bytes: int = 0
    total_bytes_in_window: int = 0
    sensitive_files_in_window: int = 0

    # File metadata (context only, no content)
    file_name: str | None = None
    file_hash: str | None = None

    # Process info
    process_name: str | None = None
    process_id: int | None = None

    # Event identity
    event_id: str | None = None


# ═════════════════════════════════════════════════════════════════════════════
#  Output: per-factor breakdown
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class RiskFactorResult:
    """One component of the risk breakdown."""
    name: str
    score: float
    weight: float
    contribution: float
    reason: str


# ═════════════════════════════════════════════════════════════════════════════
#  Output: complete assessment
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class RiskAssessmentOutput:
    """The full output of the risk engine.  Framework-agnostic."""
    risk_score: float
    risk_level: str
    factors: list[RiskFactorResult]
    explanation: str
    engine_version: str
    config_version: str


# ═════════════════════════════════════════════════════════════════════════════
#  Risk Engine
# ═════════════════════════════════════════════════════════════════════════════

class RiskEngine:
    """Deterministic, explainable, configurable risk-scoring engine.

    Usage::

        engine = RiskEngine()  # uses default config
        ctx = RiskContext(sensitivity_level="HIGHLY_CONFIDENTIAL", ...)
        result = engine.assess(ctx)
        print(result.risk_score, result.risk_level)
    """

    def __init__(self, config: RiskConfig | None = None) -> None:
        self._config = config or get_default_risk_config()
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Risk configuration is invalid: {errors}")

    @property
    def config(self) -> RiskConfig:
        return self._config

    @property
    def version(self) -> str:
        return RISK_ENGINE_VERSION

    # ── Public API ───────────────────────────────────────────────────────

    def assess(self, context: RiskContext) -> RiskAssessmentOutput:
        """Evaluate the risk of an operation described by *context*.

        Returns a deterministic, explainable ``RiskAssessmentOutput``.
        """
        cfg = self._config
        factors: list[RiskFactorResult] = []

        # 1. Sensitivity
        sens_score, sens_reason = calculate_sensitivity_score(
            context.sensitivity_level,
            context.sensitivity_categories,
            context.classification_confidence,
            cfg,
        )
        factors.append(self._factor("data_sensitivity", sens_score, "sensitivity", sens_reason, cfg))

        # 2. Action
        act_score, act_reason = calculate_action_score(context.action_type, cfg)
        factors.append(self._factor("action", act_score, "action", act_reason, cfg))

        # 3. Destination
        dest_score, dest_reason = calculate_destination_score(context.destination_type, cfg)
        factors.append(self._factor("destination", dest_score, "destination", dest_reason, cfg))

        # 4. User context
        user_score, user_reason = calculate_user_context_score(context.user_role, cfg)
        factors.append(self._factor("user_context", user_score, "user_context", user_reason, cfg))

        # 5. Device context
        dev_score, dev_reason = calculate_device_context_score(context.device_trust, cfg)
        factors.append(self._factor("device_context", dev_score, "device_context", dev_reason, cfg))

        # 6. Behavioral
        behav_score, behav_reason = calculate_behavior_score(
            context.recent_sensitive_ops,
            context.recent_total_ops,
            context.rapid_operations,
            context.unusual_destination,
            context.multiple_sensitive_files,
            cfg,
        )
        factors.append(self._factor("behavior", behav_score, "behavior", behav_reason, cfg))

        # 7. Time context
        time_score, time_reason = calculate_time_context_score(
            context.timestamp,
            context.is_business_hours,
            context.is_weekend,
            cfg,
        )
        factors.append(self._factor("time_context", time_score, "time_context", time_reason, cfg))

        # 8. Volume
        vol_score, vol_reason = calculate_volume_score(
            context.file_size_bytes,
            context.total_bytes_in_window,
            context.sensitive_files_in_window,
            cfg,
        )
        factors.append(self._factor("volume", vol_score, "volume", vol_reason, cfg))

        # ── Weighted sum ─────────────────────────────────────────────────
        total = sum(f.contribution for f in factors)
        final_score = max(0.0, min(100.0, round(total, 2)))

        # ── Risk level ───────────────────────────────────────────────────
        risk_level = self._determine_level(final_score)

        # ── Explanation ──────────────────────────────────────────────────
        explanation = self._build_explanation(final_score, risk_level, factors, context)

        return RiskAssessmentOutput(
            risk_score=final_score,
            risk_level=risk_level,
            factors=factors,
            explanation=explanation,
            engine_version=RISK_ENGINE_VERSION,
            config_version=cfg.config_version,
        )

    # ── Internals ────────────────────────────────────────────────────────

    def _factor(
        self,
        name: str,
        score: float,
        weight_key: str,
        reason: str,
        cfg: RiskConfig,
    ) -> RiskFactorResult:
        weight = cfg.risk_weights.get(weight_key, 0.0)
        contribution = round(score * weight, 2)
        return RiskFactorResult(
            name=name,
            score=round(score, 2),
            weight=weight,
            contribution=contribution,
            reason=reason,
        )

    def _determine_level(self, score: float) -> str:
        """Map a numeric score to a risk level using the configured thresholds."""
        for level_name, threshold in self._config.risk_levels.items():
            if threshold.min_score <= score <= threshold.max_score:
                return level_name
        # Fail-safe: if somehow no level matches, return HIGH
        logger.warning("Score %.2f did not match any risk level — defaulting to HIGH", score)
        return RiskLevel.HIGH

    def _build_explanation(
        self,
        score: float,
        level: str,
        factors: list[RiskFactorResult],
        context: RiskContext,
    ) -> str:
        """Build a human-readable explanation of the risk assessment."""
        parts: list[str] = []

        # Top contributing factors
        sorted_factors = sorted(factors, key=lambda f: f.contribution, reverse=True)
        significant = [f for f in sorted_factors if f.contribution > 0]

        if context.file_name:
            parts.append(f"File: {context.file_name}")

        parts.append(f"Risk score: {score:.1f} ({level})")

        if significant:
            parts.append("Key factors:")
            for f in significant[:4]:
                parts.append(f"  - {f.name}: {f.reason} (contribution: {f.contribution:.1f})")

        return "\n".join(parts)
