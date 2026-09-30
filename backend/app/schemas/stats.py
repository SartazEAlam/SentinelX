"""Dashboard statistics schemas — enhanced for Phase 6."""

from pydantic import BaseModel


class EventTrend(BaseModel):
    """Daily or hourly trend data point."""

    timestamp: str
    count: int


class OverviewStats(BaseModel):
    """Aggregated dashboard statistics."""

    total_devices: int
    active_devices: int
    total_events_24h: int
    critical_alerts: int
    pending_approvals: int
    events_trend: list[EventTrend]
    top_violators: list[dict[str, int | str]]


class DashboardSummary(BaseModel):
    """Main dashboard summary cards."""

    connected_devices: int
    events_today: int
    high_risk_events: int
    blocked_operations: int
    pending_approvals: int
    active_alerts: int


class RiskDistribution(BaseModel):
    """Risk level distribution."""

    low: int = 0
    medium: int = 0
    high: int = 0


class SensitivityDistribution(BaseModel):
    """Data sensitivity distribution from classifications."""

    public: int = 0
    internal: int = 0
    confidential: int = 0
    highly_confidential: int = 0
    unknown: int = 0


class EnforcementStats(BaseModel):
    """Enforcement outcome statistics."""

    allowed: int = 0
    held: int = 0
    blocked: int = 0
    approved: int = 0
    denied: int = 0
    expired: int = 0
    failed: int = 0
