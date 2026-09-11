"""SecurityEvent model — the central event table for DLP telemetry."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SecurityEvent(Base):
    """A single security event reported by an endpoint agent.

    Stores metadata about file operations, network activity, and other
    security-relevant actions. Does NOT store actual file contents.
    """

    __tablename__ = "security_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Event classification
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # File metadata
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Classification & risk
    sensitivity_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Context
    user_context: Mapped[str | None] = mapped_column(String(128), nullable=True)
    process_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    process_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Flexible metadata (JSON)
    metadata_json: Mapped[Any | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_events_event_id", "event_id"),
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_risk_score", "risk_score"),
        Index("ix_events_decision", "decision"),
        Index("ix_events_sensitivity", "sensitivity_level"),
        Index("ix_events_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} event_id={self.event_id!r} type={self.event_type}>"
