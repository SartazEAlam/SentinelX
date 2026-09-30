"""Risk factors — individual risk component calculators.

Each function takes relevant context + configuration and returns a normalized
score (0–100) and a human-readable reason.  These are the building blocks
combined by the risk engine.

Design:
  * Every factor function is stateless and deterministic.
  * No database access — all data is passed in via structured contexts.
  * All scores are clamped to [0, 100].
"""

from __future__ import annotations

from datetime import datetime

from app.risk_policy_config.risk_config import (
    BusinessHoursConfig,
    RiskConfig,
    TimeContext,
    VolumeSizeCategory,
)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ═════════════════════════════════════════════════════════════════════════════
#  1. Data Sensitivity
# ═════════════════════════════════════════════════════════════════════════════

def calculate_sensitivity_score(
    sensitivity_level: str,
    categories: list[str],
    confidence: float,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the data-sensitivity risk component.

    Formula:
        base = sensitivity_risk[level]
        bonus = min(sum(category_risk[c] for c in categories), max_category_bonus)
        score = clamp(base + bonus, 0, 100)

    The confidence from the classifier is used to scale the score when
    confidence < 1.0 — this prevents a low-confidence classification from
    inflating risk unduly.

    Returns:
        (score, reason)
    """
    level = sensitivity_level.upper() if sensitivity_level else config.unknown_sensitivity_fallback
    base = config.sensitivity_risk.get(level, config.sensitivity_risk.get("UNKNOWN", 30))

    # Category bonus (capped)
    bonus = 0
    matched_cats: list[str] = []
    for cat in categories:
        cat_upper = cat.upper()
        cat_score = config.category_risk.get(cat_upper, 0)
        if cat_score > 0:
            bonus += cat_score
            matched_cats.append(cat_upper)
    bonus = min(bonus, config.max_category_bonus)

    raw_score = base + bonus

    # Scale by confidence (minimum floor at 0.3 to prevent zeroing out)
    effective_confidence = max(confidence, 0.3) if confidence > 0 else 0.5
    score = _clamp(raw_score * effective_confidence)

    reason_parts = [f"Sensitivity level: {level} (base={base})"]
    if matched_cats:
        reason_parts.append(f"Categories: {', '.join(matched_cats)} (bonus={bonus})")
    if confidence < 1.0:
        reason_parts.append(f"Confidence scaling: {effective_confidence:.2f}")

    return score, "; ".join(reason_parts)


# ═════════════════════════════════════════════════════════════════════════════
#  2. Action Risk
# ═════════════════════════════════════════════════════════════════════════════

def calculate_action_score(
    action_type: str,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the action-risk component.

    Returns:
        (score, reason)
    """
    action = action_type.upper() if action_type else config.unknown_action_fallback
    score = float(config.action_risk.get(action, config.action_risk.get("UNKNOWN", 50)))
    return _clamp(score), f"Action: {action} (score={score:.0f})"


# ═════════════════════════════════════════════════════════════════════════════
#  3. Destination Risk
# ═════════════════════════════════════════════════════════════════════════════

def calculate_destination_score(
    destination_type: str,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the destination-risk component.

    Returns:
        (score, reason)
    """
    dest = destination_type.upper() if destination_type else config.unknown_destination_fallback
    score = float(config.destination_risk.get(dest, config.destination_risk.get("UNKNOWN", 50)))
    return _clamp(score), f"Destination: {dest} (score={score:.0f})"


# ═════════════════════════════════════════════════════════════════════════════
#  4. User Context
# ═════════════════════════════════════════════════════════════════════════════

def calculate_user_context_score(
    user_role: str,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the user-context risk component.

    Returns:
        (score, reason)
    """
    role = user_role.upper() if user_role else config.unknown_user_fallback
    score = float(config.user_role_risk.get(role, config.user_role_risk.get("UNKNOWN", 50)))
    return _clamp(score), f"User role: {role} (score={score:.0f})"


# ═════════════════════════════════════════════════════════════════════════════
#  5. Device Context
# ═════════════════════════════════════════════════════════════════════════════

def calculate_device_context_score(
    device_trust: str,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the device-context risk component.

    Returns:
        (score, reason)
    """
    trust = device_trust.upper() if device_trust else config.unknown_device_fallback
    score = float(config.device_trust_risk.get(trust, config.device_trust_risk.get("UNKNOWN", 50)))
    return _clamp(score), f"Device trust: {trust} (score={score:.0f})"


# ═════════════════════════════════════════════════════════════════════════════
#  6. Behavioral / Contextual Risk
# ═════════════════════════════════════════════════════════════════════════════

def calculate_behavior_score(
    recent_sensitive_ops: int,
    recent_total_ops: int,
    rapid_operations: bool,
    unusual_destination: bool,
    multiple_sensitive_files: bool,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the behavioral-context risk component.

    This uses measurable signals — not speculation.  Each signal contributes
    an additive component that is capped at 100.

    Signals and default contributions:
      - High frequency operations (>= threshold): +30
      - Rapid repeated operations:                  +15
      - Unusual destination:                        +15
      - Multiple sensitive files:                   +20
      - Per-additional-sensitive-op above threshold: +2 (max +20)
    """
    thresholds = config.behavior_thresholds
    score = 0.0
    reasons: list[str] = []

    # High-frequency operations
    if recent_sensitive_ops >= thresholds.high_frequency_ops:
        score += 30
        reasons.append(
            f"High-frequency: {recent_sensitive_ops} sensitive ops "
            f"(threshold={thresholds.high_frequency_ops})"
        )

    # Excess sensitive ops bonus
    excess = max(0, recent_sensitive_ops - thresholds.high_frequency_ops)
    if excess > 0:
        excess_bonus = min(excess * 2, 20)
        score += excess_bonus
        reasons.append(f"Excess sensitive ops bonus: +{excess_bonus}")

    if rapid_operations:
        score += 15
        reasons.append("Rapid repeated operations detected")

    if unusual_destination:
        score += 15
        reasons.append("Unusual destination detected")

    if multiple_sensitive_files:
        score += 20
        reasons.append("Multiple sensitive files in operation")

    if not reasons:
        reasons.append("Normal behavioral pattern")

    return _clamp(score), "; ".join(reasons)


# ═════════════════════════════════════════════════════════════════════════════
#  7. Time Context
# ═════════════════════════════════════════════════════════════════════════════

def determine_time_context(
    timestamp: datetime | None,
    business_hours_cfg: BusinessHoursConfig,
) -> str:
    """Determine the time context category for a given timestamp.

    Returns one of: BUSINESS_HOURS, OUTSIDE_BUSINESS_HOURS, WEEKEND
    """
    if timestamp is None:
        return TimeContext.BUSINESS_HOURS  # neutral default

    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(business_hours_cfg.timezone)
        local_time = timestamp.astimezone(tz)
    except Exception:
        local_time = timestamp

    # Check weekend
    if local_time.weekday() in business_hours_cfg.weekend_days:
        return TimeContext.WEEKEND

    # Check business hours
    start = local_time.replace(
        hour=business_hours_cfg.start_hour,
        minute=business_hours_cfg.start_minute,
        second=0, microsecond=0,
    )
    end = local_time.replace(
        hour=business_hours_cfg.end_hour,
        minute=business_hours_cfg.end_minute,
        second=0, microsecond=0,
    )

    if start <= local_time <= end:
        return TimeContext.BUSINESS_HOURS

    return TimeContext.OUTSIDE_BUSINESS_HOURS


def calculate_time_context_score(
    timestamp: datetime | None,
    is_business_hours: bool | None,
    is_weekend: bool | None,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the time-context risk component.

    If explicit flags are provided, use them; otherwise derive from timestamp.
    """
    if is_business_hours is not None:
        if is_weekend:
            context = TimeContext.WEEKEND
        elif is_business_hours:
            context = TimeContext.BUSINESS_HOURS
        else:
            context = TimeContext.OUTSIDE_BUSINESS_HOURS
    else:
        context = determine_time_context(timestamp, config.business_hours)

    score = float(config.time_context_risk.get(
        context, config.time_context_risk.get(TimeContext.BUSINESS_HOURS, 0)
    ))
    return _clamp(score), f"Time context: {context} (score={score:.0f})"


# ═════════════════════════════════════════════════════════════════════════════
#  8. Volume / Size Risk
# ═════════════════════════════════════════════════════════════════════════════

def classify_volume(
    file_size_bytes: int,
    config: RiskConfig,
) -> str:
    """Classify a transfer volume into a size category."""
    thresholds = config.volume_thresholds
    if file_size_bytes <= thresholds.small_max:
        return VolumeSizeCategory.SMALL
    if file_size_bytes <= thresholds.medium_max:
        return VolumeSizeCategory.MEDIUM
    if file_size_bytes <= thresholds.large_max:
        return VolumeSizeCategory.LARGE
    return VolumeSizeCategory.VERY_LARGE


def calculate_volume_score(
    file_size_bytes: int,
    total_bytes_in_window: int,
    sensitive_files_in_window: int,
    config: RiskConfig,
) -> tuple[float, str]:
    """Calculate the volume risk component.

    Uses the larger of (single-file category, aggregate-window category) to
    capture both single large transfers and cumulative exfiltration patterns.
    """
    # Single file category
    file_cat = classify_volume(file_size_bytes, config)
    file_score = float(config.volume_risk.get(file_cat, 5))

    # Aggregate window category
    window_cat = classify_volume(total_bytes_in_window, config)
    window_score = float(config.volume_risk.get(window_cat, 5))

    # Bonus for many sensitive files
    sensitive_bonus = min(sensitive_files_in_window * 3, 20)

    score = _clamp(max(file_score, window_score) + sensitive_bonus)

    reasons: list[str] = [f"File volume: {file_cat} ({file_size_bytes} bytes)"]
    if total_bytes_in_window > file_size_bytes:
        reasons.append(f"Window volume: {window_cat} ({total_bytes_in_window} bytes)")
    if sensitive_bonus > 0:
        reasons.append(f"Sensitive files in window: {sensitive_files_in_window} (bonus={sensitive_bonus})")

    return score, "; ".join(reasons)
