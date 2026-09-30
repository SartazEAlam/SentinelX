"""BLOCK handler — prevents the operation from completing.

For controlled SentinelX transfers, ensures no destination copy exists.
For passive detection, records the block event.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from sentinel_agent.enforcement.models import Decision, EnforcementResult, EnforcementStatus

logger = logging.getLogger(__name__)


class BlockHandler:
    """Handles BLOCK decisions — prevents the transfer.

    For controlled operations: ensures the destination file does NOT exist.
    For passively detected operations: records the block and attempts cleanup.
    """

    def handle(
        self,
        operation_id: str,
        source_path: str,
        destination: str,
        source_hash: str = "",
        controlled: bool = False,
        reason: str = "",
    ) -> EnforcementResult:
        """Process a BLOCK decision.

        Args:
            operation_id: Unique operation identifier.
            source_path: Path to the source file.
            destination: Target destination path.
            source_hash: Pre-computed source hash.
            controlled: True for SentinelX-controlled transfers (pre-evaluation).
            reason: Explanation of why the operation was blocked.

        Returns:
            EnforcementResult with BLOCKED status.
        """
        started_at = datetime.now(UTC)

        if controlled:
            # For controlled transfers, the destination write has NOT happened yet.
            # We simply refuse to execute it.
            logger.info(
                "BLOCK (controlled): operation %s prevented — %s",
                operation_id[:12],
                Path(source_path).name if source_path else "unknown",
            )
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.BLOCKED,
                decision=Decision.BLOCK,
                started_at=started_at,
                source_hash=source_hash,
                reason_code="BLOCKED",
                message=reason or "Operation blocked by policy — transfer prevented",
            )

        # For passively detected operations, the OS may have already started/completed
        # the transfer. Attempt to clean up the destination if it exists.
        cleanup_result = self._attempt_destination_cleanup(destination, operation_id)

        logger.info(
            "BLOCK (passive): operation %s — %s (cleanup=%s)",
            operation_id[:12],
            Path(source_path).name if source_path else "unknown",
            "success" if cleanup_result else "skipped/failed",
        )

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.BLOCKED,
            decision=Decision.BLOCK,
            started_at=started_at,
            source_hash=source_hash,
            reason_code="BLOCKED",
            message=reason or "Operation blocked by policy"
            + (
                " — destination cleaned"
                if cleanup_result
                else " — passive detection (cleanup not guaranteed)"
            ),
        )

    def _attempt_destination_cleanup(
        self,
        destination: str,
        operation_id: str,
    ) -> bool:
        """Attempt to remove a destination file that should not exist.

        Only removes the specific file — never recursive deletion.
        Returns True if the file was removed or doesn't exist.
        """
        if not destination:
            return False

        dest_path = Path(destination)
        try:
            if dest_path.exists() and dest_path.is_file():
                dest_path.unlink()
                logger.info(
                    "Cleaned blocked destination for operation %s: %s",
                    operation_id[:12],
                    dest_path.name,
                )
                return True
            return True  # File doesn't exist — goal achieved
        except (OSError, PermissionError) as exc:
            logger.warning(
                "Could not clean blocked destination %s: %s",
                dest_path,
                exc,
            )
            return False
