"""Dashboard statistics service — enhanced for Phase 6.

Provides aggregated metrics for the administrator dashboard using real
database records from Phases 1–5.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.approval import ApprovalRequest
from app.models.classification import Classification
from app.models.device import Device
from app.models.enforcement import EnforcementResultRecord
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    ApprovalStatus,
    DeviceStatus,
    SensitivityLevel,
)
from app.models.risk_assessment import RiskAssessment
from app.models.security_event import SecurityEvent
from app.schemas.stats import (
    DashboardSummary,
    EnforcementStats,
    EventTrend,
    OverviewStats,
    RiskDistribution,
    SensitivityDistribution,
)


def get_overview_stats(db: Session) -> OverviewStats:
    """Calculate aggregated statistics for the dashboard."""
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)

    total_devices = db.query(Device).count()
    active_devices = (
        db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
    )

    total_events_24h = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.timestamp >= day_ago)
        .count()
    )

    critical_alerts = (
        db.query(Alert)
        .filter(
            Alert.status == AlertStatus.OPEN,
            Alert.severity == AlertSeverity.CRITICAL,
        )
        .count()
    )

    pending_approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == ApprovalStatus.PENDING)
        .count()
    )

    events = (
        db.query(SecurityEvent.timestamp)
        .filter(SecurityEvent.timestamp >= day_ago)
        .all()
    )

    buckets: dict[str, int] = {}
    for i in range(24):
        bucket_time = (now - timedelta(hours=i)).replace(
            minute=0, second=0, microsecond=0
        )
        buckets[bucket_time.isoformat()] = 0

    for (ts,) in events:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        bucket_time = ts.replace(minute=0, second=0, microsecond=0)
        key = bucket_time.isoformat()
        if key in buckets:
            buckets[key] += 1

    events_trend = [
        EventTrend(timestamp=k, count=v) for k, v in sorted(buckets.items())
    ]

    top_devices = (
        db.query(
            SecurityEvent.device_id,
            func.count(SecurityEvent.id).label("count"),
        )
        .group_by(SecurityEvent.device_id)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    top_violators = []
    for device_id, count in top_devices:
        device = (
            db.query(Device.device_name)
            .filter(Device.device_id == device_id)
            .first()
        )
        name = device[0] if device else "Unknown"
        top_violators.append(
            {"device_id": device_id, "device_name": name, "event_count": count}
        )

    return OverviewStats(
        total_devices=total_devices,
        active_devices=active_devices,
        total_events_24h=total_events_24h,
        critical_alerts=critical_alerts,
        pending_approvals=pending_approvals,
        events_trend=events_trend,
        top_violators=top_violators,
    )


def get_dashboard_summary(db: Session) -> DashboardSummary:
    """Get the main dashboard summary cards."""
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)

    connected_devices = (
        db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()
    )

    events_today = (
        db.query(SecurityEvent)
        .filter(SecurityEvent.timestamp >= day_ago)
        .count()
    )

    high_risk_events = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.timestamp >= day_ago,
            SecurityEvent.risk_score >= 70,
        )
        .count()
    )

    blocked_operations = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.timestamp >= day_ago,
            SecurityEvent.decision == "BLOCK",
        )
        .count()
    )

    pending_approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == ApprovalStatus.PENDING)
        .count()
    )

    active_alerts = (
        db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()
    )

    return DashboardSummary(
        connected_devices=connected_devices,
        events_today=events_today,
        high_risk_events=high_risk_events,
        blocked_operations=blocked_operations,
        pending_approvals=pending_approvals,
        active_alerts=active_alerts,
    )


def get_risk_distribution(
    db: Session, period: str = "24h"
) -> RiskDistribution:
    """Get risk level distribution over a time range."""
    now = datetime.now(UTC)

    if period == "7d":
        since = now - timedelta(days=7)
    elif period == "30d":
        since = now - timedelta(days=30)
    else:
        since = now - timedelta(days=1)

    assessments = (
        db.query(RiskAssessment.risk_level)
        .filter(RiskAssessment.created_at >= since)
        .all()
    )

    low = sum(1 for (lvl,) in assessments if lvl == "LOW")
    medium = sum(1 for (lvl,) in assessments if lvl == "MEDIUM")
    high = sum(1 for (lvl,) in assessments if lvl == "HIGH")

    return RiskDistribution(low=low, medium=medium, high=high)


def get_sensitivity_distribution(db: Session) -> SensitivityDistribution:
    """Get data sensitivity distribution from classifications."""
    results = (
        db.query(
            Classification.sensitivity_level,
            func.count(Classification.id),
        )
        .group_by(Classification.sensitivity_level)
        .all()
    )

    dist = SensitivityDistribution()
    for level, count in results:
        level_upper = level.upper() if isinstance(level, str) else level
        if level_upper == SensitivityLevel.PUBLIC:
            dist.public = count
        elif level_upper == SensitivityLevel.INTERNAL:
            dist.internal = count
        elif level_upper == SensitivityLevel.CONFIDENTIAL:
            dist.confidential = count
        elif level_upper == SensitivityLevel.HIGHLY_CONFIDENTIAL:
            dist.highly_confidential = count
        else:
            dist.unknown = count

    return dist


def get_enforcement_stats(db: Session) -> EnforcementStats:
    """Get enforcement outcome statistics."""
    results = (
        db.query(
            EnforcementResultRecord.decision,
            EnforcementResultRecord.status,
            func.count(EnforcementResultRecord.id),
        )
        .group_by(EnforcementResultRecord.decision, EnforcementResultRecord.status)
        .all()
    )

    stats = EnforcementStats()
    for decision, status_val, count in results:
        d = decision.upper() if decision else ""
        s = status_val.upper() if status_val else ""

        if d == "ALLOW":
            stats.allowed += count
        elif d == "HOLD":
            stats.held += count
        elif d == "BLOCK":
            stats.blocked += count

        if s == "APPROVED":
            stats.approved += count
        elif s == "DENIED":
            stats.denied += count
        elif s == "EXPIRED":
            stats.expired += count
        elif s == "FAILED":
            stats.failed += count

    return stats
