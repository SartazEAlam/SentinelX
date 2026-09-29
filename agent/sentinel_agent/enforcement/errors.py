"""Enforcement error codes and structured exceptions.

Machine-readable error codes for all enforcement failure modes.
"""

from enum import StrEnum


class EnforcementErrorCode(StrEnum):
    """Stable error codes for enforcement failures."""

    ENFORCEMENT_TIMEOUT = "ENFORCEMENT_TIMEOUT"
    DESTINATION_UNAVAILABLE = "DESTINATION_UNAVAILABLE"
    USB_REMOVED = "USB_REMOVED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    STAGING_FAILED = "STAGING_FAILED"
    HASH_MISMATCH = "HASH_MISMATCH"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    DECISION_EXPIRED = "DECISION_EXPIRED"
    INVALID_DECISION = "INVALID_DECISION"
    SERVER_UNAVAILABLE = "SERVER_UNAVAILABLE"
    POLICY_REJECTED = "POLICY_REJECTED"
    CLEANUP_FAILED = "CLEANUP_FAILED"
    OPERATION_NOT_FOUND = "OPERATION_NOT_FOUND"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    STAGING_FULL = "STAGING_FULL"
    DISK_FULL = "DISK_FULL"
    PATH_TRAVERSAL = "PATH_TRAVERSAL"
    SYMLINK_UNSAFE = "SYMLINK_UNSAFE"
    REPLAY_DETECTED = "REPLAY_DETECTED"
    DESTINATION_MISMATCH = "DESTINATION_MISMATCH"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    TRANSFER_INTERRUPTED = "TRANSFER_INTERRUPTED"
    NETWORK_UNAVAILABLE = "NETWORK_UNAVAILABLE"


class EnforcementError(Exception):
    """Base enforcement exception with structured error code."""

    def __init__(
        self,
        message: str,
        code: EnforcementErrorCode = EnforcementErrorCode.ENFORCEMENT_TIMEOUT,
        operation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.operation_id = operation_id


class StagingError(EnforcementError):
    """Staging-specific failure."""

    def __init__(self, message: str, operation_id: str | None = None) -> None:
        super().__init__(message, EnforcementErrorCode.STAGING_FAILED, operation_id)


class HashMismatchError(EnforcementError):
    """Integrity validation failure."""

    def __init__(self, message: str, operation_id: str | None = None) -> None:
        super().__init__(message, EnforcementErrorCode.HASH_MISMATCH, operation_id)


class DestinationUnavailableError(EnforcementError):
    """Target destination is not accessible."""

    def __init__(self, message: str, operation_id: str | None = None) -> None:
        super().__init__(message, EnforcementErrorCode.DESTINATION_UNAVAILABLE, operation_id)


class DecisionExpiredError(EnforcementError):
    """Server decision has expired."""

    def __init__(self, message: str, operation_id: str | None = None) -> None:
        super().__init__(message, EnforcementErrorCode.DECISION_EXPIRED, operation_id)


class InvalidStateTransitionError(EnforcementError):
    """Attempted illegal state transition."""

    def __init__(self, message: str, operation_id: str | None = None) -> None:
        super().__init__(message, EnforcementErrorCode.INVALID_STATE_TRANSITION, operation_id)
