"""Rollback manager — cleanup for partial, failed, and expired operations.

Conservative: only operates on SentinelX-owned staging paths.
Never performs recursive deletion on arbitrary paths.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sentinel_agent.enforcement.staging import StagingManager

logger = logging.getLogger(__name__)


class RollbackManager:
    """Handles cleanup and rollback of enforcement operations."""

    def __init__(self, staging_manager: StagingManager) -> None:
        self._staging = staging_manager

    def rollback_staged_operation(self, operation_id: str, reason: str = "") -> bool:
        """Roll back a staged operation by removing the staging file.

        Returns True if cleanup succeeded.
        """
        try:
            self._staging.cancel_staged_operation(operation_id, reason)
            logger.info(
                "Rolled back staged operation %s: %s",
                operation_id[:12],
                reason or "no reason",
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to rollback operation %s: %s",
                operation_id[:12],
                exc,
            )
            return False

    def cleanup_partial_transfer(
        self,
        destination: str,
        operation_id: str,
    ) -> bool:
        """Clean up a partial destination file from a failed transfer.

        Only removes the specific destination file, never recursive.

        Returns True if cleanup succeeded or nothing to clean.
        """
        dest_path = Path(destination)
        try:
            if dest_path.exists() and dest_path.is_file():
                dest_path.unlink()
                logger.info(
                    "Cleaned partial transfer for operation %s: %s",
                    operation_id[:12],
                    dest_path.name,
                )
                return True
            return True  # Nothing to clean
        except (OSError, PermissionError) as exc:
            logger.error(
                "Cannot clean partial transfer %s: %s",
                dest_path,
                exc,
            )
            return False

    def cleanup_expired_operations(self) -> list[str]:
        """Clean up all expired staging operations.

        Returns list of cleaned operation IDs.
        """
        return self._staging.cleanup_expired()

    def cleanup_all_staging(self) -> int:
        """Emergency cleanup of all staging files (crash recovery).

        Returns number of files cleaned.
        """
        return self._staging.cleanup_all()
