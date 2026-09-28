"""RiskAssessment model — persistent, immutable record of a risk evaluation.

Each assessment captures the exact score, factors, engine/config versions,
and policy decision that was computed for a specific security event.
Historical assessments are NEVER overwritten; a new row is created if
re-evaluation is needed.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskAssessment(Base):
    """Immutable risk assessment result for a security event."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Links back to the event (by event_id string, not FK, to keep decoupled
    # and to preserve assessments even if events are pruned)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # ── Versioning (immutability) ────────────────────────────────────────
    risk_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    policy_engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_config_version: Mapped[str] = mapped_column(String(32), nullable=False)

    # ── Computed scores ──────────────────────────────────────────────────
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)

    # ── Policy decision ──────────────────────────────────────────────────
    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # ALLOW | HOLD | BLOCK
    policy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    policy_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Explainable breakdown (JSON-encoded list of factor dicts) ────────
    factor_breakdown_json: Mapped[Any | None] = mapped_column(Text, nullable=True)

    # ── Human-readable explanation ───────────────────────────────────────
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamp ────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_risk_assessments_risk_level", "risk_level"),
        Index("ix_risk_assessments_decision", "decision"),
        Index("ix_risk_assessments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskAssessment id={self.id} event_id={self.event_id!r} "
            f"score={self.risk_score} decision={self.decision}>"
        )
