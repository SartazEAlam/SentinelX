"""Secure staging area — temporary holding for HOLD operations.

Manages a dedicated staging directory with:
- Randomized filenames (no user-controlled path components)
- Restrictive permissions
- Size limits and automatic expiration
- Integrity verification via SHA-256
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sentinel_agent.enforcement.errors import (
    EnforcementError,
    EnforcementErrorCode,
    StagingError,
)
from sentinel_agent.enforcement.models import StagingRecord
from sentinel_agent.enforcement.safety import (
    set_restrictive_permissions,
    validate_file_size,
    validate_path_safety,
    validate_staging_capacity,
)

logger = logging.getLogger(__name__)


class StagingManager:
    """Manages the secure staging area for HOLD operations.

    Files are staged with randomized names inside a controlled directory.
    The manager tracks metadata and enforces size/expiration limits.
    """

    def __init__(
        self,
        staging_dir: Path,
        max_file_size_mb: int = 100,
        max_total_size_mb: int = 500,
        default_expiry_seconds: int = 300,
    ) -> None:
        self._staging_dir = staging_dir.resolve()
        self._max_file_size_mb = max_file_size_mb
        self._max_total_mb = max_total_size_mb
        self._default_expiry_seconds = default_expiry_seconds
        self._records: dict[str, StagingRecord] = {}

        # Ensure staging directory exists with restrictive permissions
        self._staging_dir.mkdir(parents=True, exist_ok=True)
        set_restrictive_permissions(self._staging_dir)

    @property
    def staging_dir(self) -> Path:
        return self._staging_dir

    @property
    def active_records(self) -> list[StagingRecord]:
        return [r for r in self._records.values() if r.status == "STAGED"]

    def stage_file(
        self,
        source_path: str | Path,
        operation_id: str,
        event_id: str,
        destination: str,
        source_hash: str = "",
        expiry_seconds: int | None = None,
    ) -> StagingRecord:
        """Stage a file for a HOLD operation.

        Copies the source file to the staging area with a randomized name.
        Validates size, capacity, and integrity.

        Returns:
            StagingRecord with metadata about the staged file.

        Raises:
            StagingError: If staging fails.
        """
        source = Path(source_path).resolve()

        if not source.exists():
            raise StagingError(
                f"Source file not found: {source}",
                operation_id=operation_id,
            )

        if not source.is_file():
            raise StagingError(
                f"Source is not a file: {source}",
                operation_id=operation_id,
            )

        # Get file size
        try:
            file_size = source.stat().st_size
        except OSError as exc:
            raise StagingError(
                f"Cannot stat source file: {exc}",
                operation_id=operation_id,
            ) from exc

        # Validate size limits
        try:
            validate_file_size(file_size, self._max_file_size_mb)
            validate_staging_capacity(self._staging_dir, file_size, self._max_total_mb)
        except EnforcementError as exc:
            raise StagingError(
                str(exc),
                operation_id=operation_id,
            ) from exc

        # Generate secure staging filename
        staging_id = str(uuid.uuid4())
        # Preserve extension for audit but use random name
        suffix = source.suffix or ""
        staging_filename = f"{staging_id}{suffix}"
        staging_path = self._staging_dir / staging_filename

        # Validate staging path stays inside staging dir
        staging_path = validate_path_safety(staging_path, self._staging_dir)

        # Compute source hash if not provided
        if not source_hash:
            source_hash = self._compute_hash(source)

        # Copy file to staging
        try:
            shutil.copy2(str(source), str(staging_path))
            set_restrictive_permissions(staging_path)
        except (OSError, PermissionError, shutil.Error) as exc:
            # Clean up partial copy
            try:
                if staging_path.exists():
                    staging_path.unlink()
            except OSError:
                pass
            raise StagingError(
                f"Failed to stage file: {exc}",
                operation_id=operation_id,
            ) from exc

        # Verify staged copy integrity
        staged_hash = self._compute_hash(staging_path)
        if staged_hash != source_hash:
            # Clean up corrupt copy
            try:
                staging_path.unlink()
            except OSError:
                pass
            raise StagingError(
                f"Staged file hash mismatch: source={source_hash[:16]}… "
                f"staged={staged_hash[:16]}…",
                operation_id=operation_id,
            )

        # Calculate expiration
        expiry = expiry_seconds or self._default_expiry_seconds
        expires_at = datetime.now(UTC) + timedelta(seconds=expiry)

        record = StagingRecord(
            staging_id=staging_id,
            operation_id=operation_id,
            event_id=event_id,
            source_path=str(source),
            source_hash=source_hash,
            staging_path=str(staging_path),
            destination=destination,
            file_size=file_size,
            expires_at=expires_at,
            status="STAGED",
        )

        self._records[operation_id] = record
        logger.info(
            "Staged file for operation %s: %s → %s (%d bytes, expires %s)",
            operation_id[:12],
            source.name,
            staging_path.name,
            file_size,
            expires_at.isoformat(),
        )

        return record

    def get_record(self, operation_id: str) -> StagingRecord | None:
        """Retrieve a staging record by operation ID."""
        return self._records.get(operation_id)

    def complete_staged_transfer(
        self,
        operation_id: str,
        destination: str,
    ) -> tuple[str, int]:
        """Complete a staged transfer by copying from staging to the final destination.

        Returns:
            Tuple of (destination_hash, bytes_transferred).

        Raises:
            StagingError: If the transfer fails.
        """
        record = self._records.get(operation_id)
        if record is None:
            raise StagingError(
                f"No staging record for operation {operation_id}",
                operation_id=operation_id,
            )

        staging_path = Path(record.staging_path)
        if not staging_path.exists():
            raise StagingError(
                f"Staged file missing: {staging_path}",
                operation_id=operation_id,
            )

        # Verify staging integrity before transfer
        current_hash = self._compute_hash(staging_path)
        if current_hash != record.source_hash:
            raise StagingError(
                f"Staged file integrity compromised: expected {record.source_hash[:16]}… "
                f"got {current_hash[:16]}…",
                operation_id=operation_id,
            )

        # Verify destination matches approval
        if destination != record.destination:
            raise EnforcementError(
                f"Destination mismatch: approved={record.destination}, "
                f"actual={destination}",
                code=EnforcementErrorCode.DESTINATION_MISMATCH,
                operation_id=operation_id,
            )

        # Perform the actual transfer
        dest_path = Path(destination)
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(staging_path), str(dest_path))
        except (OSError, PermissionError, shutil.Error) as exc:
            raise StagingError(
                f"Failed to complete staged transfer: {exc}",
                operation_id=operation_id,
            ) from exc

        # Verify destination integrity
        dest_hash = self._compute_hash(dest_path)
        if dest_hash != record.source_hash:
            # Clean up corrupt destination
            try:
                dest_path.unlink()
            except OSError:
                pass
            raise StagingError(
                f"Destination hash mismatch: expected {record.source_hash[:16]}… "
                f"got {dest_hash[:16]}…",
                operation_id=operation_id,
            )

        bytes_transferred = dest_path.stat().st_size

        # Clean up staging
        self._cleanup_staging_file(operation_id)

        record.status = "COMPLETED"
        logger.info(
            "Staged transfer completed: operation %s → %s (%d bytes)",
            operation_id[:12],
            dest_path.name,
            bytes_transferred,
        )

        return dest_hash, bytes_transferred

    def cancel_staged_operation(self, operation_id: str, reason: str = "") -> None:
        """Cancel a staged operation and clean up."""
        self._cleanup_staging_file(operation_id)
        record = self._records.get(operation_id)
        if record:
            record.status = "CANCELLED"
            logger.info(
                "Cancelled staged operation %s%s",
                operation_id[:12],
                f": {reason}" if reason else "",
            )

    def cleanup_expired(self) -> list[str]:
        """Clean up all expired staging records.

        Returns:
            List of operation IDs that were cleaned.
        """
        now = datetime.now(UTC)
        expired_ops: list[str] = []

        for op_id, record in list(self._records.items()):
            if record.status != "STAGED":
                continue
            if record.expires_at and now >= record.expires_at:
                self._cleanup_staging_file(op_id)
                record.status = "EXPIRED"
                expired_ops.append(op_id)
                logger.info("Expired staging for operation %s", op_id[:12])

        return expired_ops

    def cleanup_all(self) -> int:
        """Clean up all staging files (shutdown/crash recovery).

        Returns:
            Number of files cleaned.
        """
        count = 0
        for op_id in list(self._records.keys()):
            self._cleanup_staging_file(op_id)
            count += 1

        # Also remove any orphaned files in the staging directory
        try:
            for f in self._staging_dir.iterdir():
                if f.is_file():
                    f.unlink()
                    count += 1
        except OSError as exc:
            logger.warning("Error cleaning staging directory: %s", exc)

        return count

    def _cleanup_staging_file(self, operation_id: str) -> None:
        """Securely remove a staged file."""
        record = self._records.get(operation_id)
        if record is None:
            return

        staging_path = Path(record.staging_path)
        try:
            if staging_path.exists():
                # Overwrite with zeros before deletion for security
                size = staging_path.stat().st_size
                if size > 0 and size < 100 * 1024 * 1024:  # Only zero-fill < 100MB
                    with open(staging_path, "wb") as f:
                        f.write(b"\x00" * size)
                staging_path.unlink()
                logger.debug("Removed staging file: %s", staging_path.name)
        except (OSError, PermissionError) as exc:
            logger.warning(
                "Could not remove staging file %s: %s",
                staging_path.name,
                exc,
            )

    @staticmethod
    def _compute_hash(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
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
