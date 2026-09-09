"""SQLAlchemy declarative base and shared model utilities.

This module defines the Base class and common mixins used across all
database models. Individual table models will be added in later phases.

Planned models (not yet implemented):
    - User
    - Device
    - SecurityEvent
    - ApprovalRequest
    - Policy
    - Alert
    - AuditLog
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all SentinelX database models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns.

    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
