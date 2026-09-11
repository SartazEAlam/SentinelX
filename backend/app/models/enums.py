"""Canonical enumeration types for all SentinelX database models.

All enums use UPPER_CASE string values for consistency across
the database, API schemas, and serialization.
"""

from enum import StrEnum


class UserRole(StrEnum):
    """Roles for administrator/analyst/viewer access control."""

    ADMIN = "ADMIN"
    SECURITY_ANALYST = "SECURITY_ANALYST"
    VIEWER = "VIEWER"


class DeviceStatus(StrEnum):
    """Operational status of a registered endpoint device."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN = "UNKNOWN"
    DISABLED = "DISABLED"


class EventType(StrEnum):
    """Categories of security events reported by endpoint agents."""

    FILE_ACCESS = "FILE_ACCESS"
    FILE_COPY = "FILE_COPY"
    FILE_MOVE = "FILE_MOVE"
    FILE_UPLOAD = "FILE_UPLOAD"
    FILE_DOWNLOAD = "FILE_DOWNLOAD"
    USB_ACTIVITY = "USB_ACTIVITY"
    NETWORK_TRANSFER = "NETWORK_TRANSFER"
    CLOUD_SYNC = "CLOUD_SYNC"
    EMAIL_ATTACHMENT = "EMAIL_ATTACHMENT"
    CLIPBOARD_ACTIVITY = "CLIPBOARD_ACTIVITY"
    PROCESS_ACTIVITY = "PROCESS_ACTIVITY"
    OTHER = "OTHER"


class EventDecision(StrEnum):
    """Decision applied to a security event by policy/classification."""

    ALLOW = "ALLOW"
    HOLD = "HOLD"
    BLOCK = "BLOCK"
    MONITOR = "MONITOR"


class SensitivityLevel(StrEnum):
    """Data sensitivity classification levels."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL"
    UNKNOWN = "UNKNOWN"


class ApprovalStatus(StrEnum):
    """Status of an approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class AlertSeverity(StrEnum):
    """Severity level of a security alert."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    """Lifecycle status of a security alert."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AuditAction(StrEnum):
    """Categories of auditable actions."""

    USER_LOGIN = "USER_LOGIN"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    DEVICE_REGISTERED = "DEVICE_REGISTERED"
    DEVICE_DISABLED = "DEVICE_DISABLED"
    DEVICE_ENABLED = "DEVICE_ENABLED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    DEVICE_HEARTBEAT = "DEVICE_HEARTBEAT"
    EVENT_CREATED = "EVENT_CREATED"
    EVENT_BATCH_CREATED = "EVENT_BATCH_CREATED"
    APPROVAL_CREATED = "APPROVAL_CREATED"
    APPROVAL_APPROVED = "APPROVAL_APPROVED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_UPDATED = "POLICY_UPDATED"
    POLICY_DELETED = "POLICY_DELETED"
    ALERT_CREATED = "ALERT_CREATED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"
    ALERT_RESOLVED = "ALERT_RESOLVED"
