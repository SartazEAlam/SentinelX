"""Dashboard statistics schemas."""

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
    top_violators: list[dict[str, int | str]]  # device_id/name -> event_count
