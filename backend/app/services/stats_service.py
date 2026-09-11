"""Dashboard statistics service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.approval import ApprovalRequest
from app.models.device import Device
from app.models.enums import AlertSeverity, AlertStatus, ApprovalStatus, DeviceStatus
from app.models.security_event import SecurityEvent
from app.schemas.stats import EventTrend, OverviewStats


def get_overview_stats(db: Session) -> OverviewStats:
    """Calculate aggregated statistics for the dashboard."""
    now = datetime.now(UTC)
    day_ago = now - timedelta(days=1)

    # 1. Device stats
    total_devices = db.query(Device).count()
    active_devices = db.query(Device).filter(Device.status == DeviceStatus.ONLINE).count()

    # 2. Event stats (last 24h)
    total_events_24h = (
        db.query(SecurityEvent).filter(SecurityEvent.timestamp >= day_ago).count()
    )

    # 3. Critical Alerts
    critical_alerts = (
        db.query(Alert)
        .filter(
            Alert.status == AlertStatus.OPEN,
            Alert.severity == AlertSeverity.CRITICAL,
        )
        .count()
    )

    # 4. Pending Approvals
    pending_approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == ApprovalStatus.PENDING)
        .count()
    )

    # 5. Events Trend (simplified: just grouping by hour for the last 24h)
    # Using SQLite/PostgreSQL compatible approach:
    # Actually, full cross-db date truncation is complex in raw SQLAlchemy without
    # specific dialects, so we'll do a simple python-side bucket for now if the
    # dataset is small, or we can use a basic query. Since Phase 1 focuses on real
    # data but simple queries, we'll fetch the timestamps and bucket them.
    # To be efficient, we only fetch the timestamp column.

    events = db.query(SecurityEvent.timestamp).filter(SecurityEvent.timestamp >= day_ago).all()

    buckets: dict[str, int] = {}
    for i in range(24):
        # Format: YYYY-MM-DDTHH:00:00Z
        bucket_time = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        buckets[bucket_time.isoformat()] = 0

    for (ts,) in events:
        # Assign to nearest hour bucket
        bucket_time = ts.replace(minute=0, second=0, microsecond=0)
        key = bucket_time.isoformat()
        if key in buckets:
            buckets[key] += 1

    events_trend = [
        EventTrend(timestamp=k, count=v) for k, v in sorted(buckets.items())
    ]

    # 6. Top Violators (Devices with most events)
    # Group by device_id
    top_devices = (
        db.query(
            SecurityEvent.device_id,
            func.count(SecurityEvent.id).label("count")
        )
        .group_by(SecurityEvent.device_id)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    top_violators = []
    for device_id, count in top_devices:
        # Get device name
        device = db.query(Device.device_name).filter(Device.device_id == device_id).first()
        name = device[0] if device else "Unknown"
        top_violators.append(
            {
                "device_id": device_id,
                "device_name": name,
                "event_count": count
            }
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
