"""Enforcement data models for the backend database."""

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnforcementResultRecord(Base):
    """Stores the final outcome of an enforcement operation reported by an agent."""

    __tablename__ = "enforcement_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operation_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False)
    
    # Status and decision
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # ALLOWED, HELD, BLOCKED, COMPLETED, FAILED, EXPIRED, DENIED
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # ALLOW, HOLD, BLOCK
    
    # Timing
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Transfer data
    source_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bytes_transferred: Mapped[int] = mapped_column(Integer, default=0)
    
    # Errors & Reasons
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "id": self.id,
            "operation_id": self.operation_id,
            "status": self.status,
            "decision": self.decision,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "source_hash": self.source_hash,
            "destination_hash": self.destination_hash,
            "bytes_transferred": self.bytes_transferred,
            "reason_code": self.reason_code,
            "error_code": self.error_code,
            "message": self.message,
        }
