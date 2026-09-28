"""ApprovalRequest model — hold/review workflow for security events.

Phase 4 extends the Phase 1 approval model with:
  - risk_assessment_id linking to the risk assessment that triggered the hold
  - requested_action — the operation that was held
  - expires_at — automatic expiry for pending approvals
  - policy_id / policy_version — tracks which policy triggered the hold
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApprovalRequest(Base):
    """An approval request tied to a specific security event.

    Approval requests allow security analysts or admins to review
    and approve/reject held security events.
    """

    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("security_events.id"), nullable=False)
    requested_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 4: link to risk assessment
    risk_assessment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requested_action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    policy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    event = relationship("SecurityEvent", foreign_keys=[event_id], lazy="joined")
    requester = relationship("User", foreign_keys=[requested_by], lazy="joined")
    reviewer = relationship("User", foreign_keys=[assigned_to], lazy="joined")

    __table_args__ = (
        Index("ix_approvals_request_id", "request_id"),
        Index("ix_approvals_status", "status"),
        Index("ix_approvals_event_id", "event_id"),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest id={self.id} request_id={self.request_id!r} status={self.status}>"
