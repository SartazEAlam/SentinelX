"""Classification model — stores sensitivity classification results for events."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.security_event import SecurityEvent


class Classification(Base):
    """A data sensitivity classification result associated with a security event."""

    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("security_events.event_id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    sensitivity_level: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # JSON-encoded lists
    categories_json: Mapped[Any | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Any | None] = mapped_column(Text, nullable=True)

    content_inspected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    inspection_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    classifier_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)

    classified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationship back to SecurityEvent
    event: Mapped["SecurityEvent"] = relationship("SecurityEvent", back_populates="classification")

    def __repr__(self) -> str:
        return f"<Classification id={self.id} event_id={self.event_id!r} sensitivity={self.sensitivity_level}>"
