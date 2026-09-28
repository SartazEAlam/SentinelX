"""Policy model — configurable DLP policy definitions.

Phase 4 extends the Phase 1 policy model with:
  - version tracking for immutable history
  - soft-delete support
  - updated_by tracking
  - richer condition fields for the policy engine
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Policy(Base):
    """A DLP policy that defines rules for event evaluation.

    Policies are evaluated by the Phase 4 policy engine.  Higher-priority
    policies are checked first; the first matching policy wins.
    """

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Policy criteria (stored as JSON strings for flexibility)
    sensitivity_levels: Mapped[Any | None] = mapped_column(Text, nullable=True)
    risk_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    allowed_actions: Mapped[Any | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)
    conditions: Mapped[Any | None] = mapped_column(Text, nullable=True)

    # Phase 4: risk-score range for policy matching
    min_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Phase 4: action/destination type conditions (JSON lists)
    action_types: Mapped[Any | None] = mapped_column(Text, nullable=True)
    destination_types: Mapped[Any | None] = mapped_column(Text, nullable=True)

    # Phase 4: version tracking — incremented on each update
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Phase 4: soft-delete support
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Ownership
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    updater = relationship("User", foreign_keys=[updated_by], lazy="joined")

    __table_args__ = (
        Index("ix_policies_name", "name"),
        Index("ix_policies_enabled", "enabled"),
        Index("ix_policies_priority", "priority"),
        Index("ix_policies_is_deleted", "is_deleted"),
    )

    def __repr__(self) -> str:
        return f"<Policy id={self.id} name={self.name!r} enabled={self.enabled} v{self.version}>"
