"""Alert model — security alerts generated from events."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    """A security alert, typically generated in response to a high-risk event.

    Alerts follow the lifecycle: OPEN → ACKNOWLEDGED → RESOLVED.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("security_events.id"), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="OPEN")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    event = relationship("SecurityEvent", foreign_keys=[event_id], lazy="joined")
    acknowledger = relationship("User", foreign_keys=[acknowledged_by], lazy="joined")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="joined")

    __table_args__ = (
        Index("ix_alerts_alert_id", "alert_id"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_device_id", "device_id"),
    )

    def __repr__(self) -> str:
        return f"<Alert id={self.id} alert_id={self.alert_id!r} severity={self.severity}>"
