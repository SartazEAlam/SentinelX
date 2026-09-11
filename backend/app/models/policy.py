"""Policy model — configurable DLP policy definitions."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Policy(Base):
    """A DLP policy that defines rules for event evaluation.

    Phase 1 only stores and manages policies.
    The actual policy evaluation engine is built in Phase 4.
    """

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Policy criteria (stored as JSON strings for flexibility)
    sensitivity_levels: Mapped[Optional[Any]] = mapped_column(Text, nullable=True)
    risk_threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    allowed_actions: Mapped[Optional[Any]] = mapped_column(Text, nullable=True)
    decision: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    conditions: Mapped[Optional[Any]] = mapped_column(Text, nullable=True)

    # Ownership
    created_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")

    __table_args__ = (
        Index("ix_policies_name", "name"),
        Index("ix_policies_enabled", "enabled"),
        Index("ix_policies_priority", "priority"),
    )

    def __repr__(self) -> str:
        return f"<Policy id={self.id} name={self.name!r} enabled={self.enabled}>"
