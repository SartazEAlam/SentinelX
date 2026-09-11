"""Device model — registered endpoint agents."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import DeviceStatus


class Device(Base):
    """A registered SentinelX endpoint device.

    Devices authenticate using a one-time token (only the hash is stored).
    The plaintext token is returned exactly once during registration.
    """

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(128), nullable=False)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    agent_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=DeviceStatus.UNKNOWN
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("ix_devices_device_id", "device_id"),
        Index("ix_devices_status", "status"),
        Index("ix_devices_is_active", "is_active"),
        Index("ix_devices_last_seen_at", "last_seen_at"),
    )

    def __repr__(self) -> str:
        return f"<Device id={self.id} device_id={self.device_id!r} status={self.status}>"
