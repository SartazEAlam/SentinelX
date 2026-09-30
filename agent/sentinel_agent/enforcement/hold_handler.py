"""HOLD handler — stages operations and waits for administrator approval.

The file is copied to a secure staging area. The destination write does NOT
occur until an administrator approves. Expired holds are treated as BLOCK.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sentinel_agent.enforcement.errors import EnforcementErrorCode, StagingError
from sentinel_agent.enforcement.models import Decision, EnforcementResult, EnforcementStatus
from sentinel_agent.enforcement.staging import StagingManager

logger = logging.getLogger(__name__)


class HoldHandler:
    """Handles HOLD decisions — stages the file and awaits approval.

    The actual destination write is deferred until approval is received.
    """

    def __init__(self, staging_manager: StagingManager) -> None:
        self._staging = staging_manager

    def hold(
        self,
        operation_id: str,
        event_id: str,
        source_path: str,
        destination: str,
        source_hash: str = "",
        approval_timeout_seconds: int = 300,
    ) -> EnforcementResult:
        """Stage the file and create a hold record.

        Returns:
            EnforcementResult with HELD status and staging metadata.
        """
        started_at = datetime.now(UTC)

        try:
            record = self._staging.stage_file(
                source_path=source_path,
                operation_id=operation_id,
                event_id=event_id,
                destination=destination,
                source_hash=source_hash,
                expiry_seconds=approval_timeout_seconds,
            )
        except StagingError as exc:
            logger.error("HOLD staging failed: %s", exc.message)
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.HOLD,
                started_at=started_at,
                error_code=exc.code.value,
                message=f"Staging failed: {exc.message}",
            )

        logger.info(
            "HOLD: operation %s staged — awaiting approval (expires %s)",
            operation_id[:12],
            record.expires_at.isoformat() if record.expires_at else "never",
        )

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.HELD,
            decision=Decision.HOLD,
            started_at=started_at,
            source_hash=record.source_hash,
            message=f"Operation held for approval (staging_id={record.staging_id[:12]}…)",
        )

    def approve(
        self,
        operation_id: str,
        destination: str,
        approval_id: str = "",
    ) -> EnforcementResult:
        """Complete a staged transfer after administrator approval.

        Validates:
        - Staging record exists and is valid
        - Destination matches the original request
        - Source integrity is preserved

        Returns:
            EnforcementResult with COMPLETED status on success.
        """
        started_at = datetime.now(UTC)

        record = self._staging.get_record(operation_id)
        if record is None:
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.HOLD,
                started_at=started_at,
                error_code=EnforcementErrorCode.OPERATION_NOT_FOUND,
                message="No staging record found for operation",
            )

        # Check expiration
        if record.expires_at and datetime.now(UTC) >= record.expires_at:
            self._staging.cancel_staged_operation(operation_id, "Expired before approval")
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.EXPIRED,
                decision=Decision.HOLD,
                started_at=started_at,
                error_code=EnforcementErrorCode.APPROVAL_EXPIRED,
                message="Approval expired — operation blocked",
            )

        try:
            dest_hash, bytes_transferred = self._staging.complete_staged_transfer(
                operation_id=operation_id,
                destination=destination,
            )
        except Exception as exc:
            logger.error("APPROVE transfer failed: %s", exc)
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.HOLD,
                started_at=started_at,
                error_code=EnforcementErrorCode.STAGING_FAILED,
                message=f"Approved transfer failed: {exc}",
            )

        logger.info(
            "APPROVED: operation %s completed (%d bytes)",
            operation_id[:12],
            bytes_transferred,
        )

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.COMPLETED,
            decision=Decision.HOLD,
            started_at=started_at,
            source_hash=record.source_hash,
            destination_hash=dest_hash,
            bytes_transferred=bytes_transferred,
            reason_code="APPROVED",
            message=f"Transfer completed after approval (approval={approval_id[:12] if approval_id else 'N/A'})",
        )

    def deny(self, operation_id: str, reason: str = "") -> EnforcementResult:
        """Deny a held operation and clean up staging.

        Returns:
            EnforcementResult with DENIED status.
        """
        started_at = datetime.now(UTC)
        record = self._staging.get_record(operation_id)

        self._staging.cancel_staged_operation(operation_id, reason or "Denied by administrator")

        logger.info(
            "DENIED: operation %s — %s",
            operation_id[:12],
            reason or "denied by administrator",
        )

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.DENIED,
            decision=Decision.HOLD,
            started_at=started_at,
            source_hash=record.source_hash if record else "",
            reason_code="DENIED",
            message=f"Operation denied: {reason or 'administrator decision'}",
        )

    def expire(self, operation_id: str) -> EnforcementResult:
        """Handle expiration of a held operation.

        Expired holds are treated as BLOCK — the staging is cleaned up.
        """
        started_at = datetime.now(UTC)
        record = self._staging.get_record(operation_id)

        self._staging.cancel_staged_operation(operation_id, "Expired")

        logger.info("EXPIRED: operation %s — treated as BLOCK", operation_id[:12])

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.EXPIRED,
            decision=Decision.HOLD,
            started_at=started_at,
            source_hash=record.source_hash if record else "",
            reason_code="EXPIRED",
            message="Approval expired — operation blocked per fail-safe policy",
        )
