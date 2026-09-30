"""ALLOW handler — lets the operation proceed normally.

Minimal intervention: verifies hash integrity and records an audit event.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path

from sentinel_agent.enforcement.errors import EnforcementErrorCode
from sentinel_agent.enforcement.models import Decision, EnforcementResult, EnforcementStatus

logger = logging.getLogger(__name__)


class AllowHandler:
    """Handles ALLOW decisions — operation proceeds normally.

    For SentinelX-controlled transfers, verifies integrity.
    For passive monitoring, simply records the allowance.
    """

    def handle(
        self,
        operation_id: str,
        source_path: str,
        destination: str,
        source_hash: str = "",
        controlled: bool = False,
    ) -> EnforcementResult:
        """Process an ALLOW decision.

        Args:
            operation_id: Unique operation identifier.
            source_path: Path to the source file.
            destination: Target destination path.
            source_hash: Pre-computed source hash.
            controlled: If True, this is a SentinelX-controlled transfer
                       (the handler performs the copy and verifies integrity).
                       If False, the transfer already happened via normal OS
                       mechanisms and we just record it.

        Returns:
            EnforcementResult with the outcome.
        """
        from datetime import UTC, datetime

        started_at = datetime.now(UTC)

        if not controlled:
            # Passive mode — the operation already completed
            logger.info(
                "ALLOW (passive): operation %s — %s",
                operation_id[:12],
                Path(source_path).name,
            )
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.ALLOWED,
                decision=Decision.ALLOW,
                started_at=started_at,
                source_hash=source_hash,
                message="Operation allowed (passive monitoring)",
            )

        # Controlled mode — perform the copy and verify integrity
        src = Path(source_path)
        dest = Path(destination)

        if not src.exists():
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.ALLOW,
                started_at=started_at,
                error_code=EnforcementErrorCode.FILE_NOT_FOUND,
                message=f"Source file not found: {src}",
            )

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
        except (OSError, PermissionError, shutil.Error) as exc:
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.ALLOW,
                started_at=started_at,
                error_code=EnforcementErrorCode.PERMISSION_DENIED,
                message=f"Transfer failed: {exc}",
            )

        # Verify integrity
        dest_hash = self._compute_hash(dest)
        bytes_transferred = dest.stat().st_size if dest.exists() else 0

        if source_hash and dest_hash != source_hash:
            # Clean up corrupt copy
            try:
                dest.unlink()
            except OSError:
                pass
            return EnforcementResult(
                operation_id=operation_id,
                status=EnforcementStatus.FAILED,
                decision=Decision.ALLOW,
                started_at=started_at,
                source_hash=source_hash,
                destination_hash=dest_hash,
                error_code=EnforcementErrorCode.HASH_MISMATCH,
                message="Destination hash does not match source",
            )

        logger.info(
            "ALLOW (controlled): operation %s — %s → %s (%d bytes)",
            operation_id[:12],
            src.name,
            dest.name,
            bytes_transferred,
        )

        return EnforcementResult(
            operation_id=operation_id,
            status=EnforcementStatus.COMPLETED,
            decision=Decision.ALLOW,
            started_at=started_at,
            source_hash=source_hash,
            destination_hash=dest_hash,
            bytes_transferred=bytes_transferred,
            message="Transfer completed with integrity verification",
        )

    @staticmethod
    def _compute_hash(path: Path) -> str:
        sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha256.update(chunk)
            return sha256.hexdigest()
        except (OSError, PermissionError):
            return ""
