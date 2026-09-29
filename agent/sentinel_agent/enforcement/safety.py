"""Safety utilities — path traversal protection, symlink checks, size limits.

All enforcement file operations pass through these validators before executing.
"""

from __future__ import annotations

import logging
import os
import stat
from pathlib import Path

from sentinel_agent.enforcement.errors import EnforcementError, EnforcementErrorCode

logger = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────

MAX_STAGING_FILE_SIZE_MB = 100
MAX_STAGING_TOTAL_SIZE_MB = 500


def validate_path_safety(path: str | Path, allowed_root: Path | None = None) -> Path:
    """Resolve and validate a path for safety.

    - Resolves symlinks and relative components
    - Checks for path traversal attempts
    - Validates the path stays within the allowed root (if given)

    Returns:
        The canonical resolved path.

    Raises:
        EnforcementError: On path traversal or unsafe path.
    """
    path = Path(path)

    # Check for obvious traversal patterns in the raw string
    path_str = str(path)
    if ".." in path_str.replace("\\", "/").split("/"):
        raise EnforcementError(
            f"Path traversal detected: {path_str}",
            code=EnforcementErrorCode.PATH_TRAVERSAL,
        )

    # Resolve to canonical absolute path
    try:
        resolved = path.resolve(strict=False)
    except (OSError, ValueError) as exc:
        raise EnforcementError(
            f"Cannot resolve path: {path_str} — {exc}",
            code=EnforcementErrorCode.PATH_TRAVERSAL,
        ) from exc

    # If an allowed root is specified, ensure the path is within it
    if allowed_root is not None:
        allowed_resolved = allowed_root.resolve(strict=False)
        try:
            resolved.relative_to(allowed_resolved)
        except ValueError:
            raise EnforcementError(
                f"Path {resolved} escapes allowed root {allowed_resolved}",
                code=EnforcementErrorCode.PATH_TRAVERSAL,
            )

    return resolved


def check_symlink_safety(path: str | Path) -> bool:
    """Check if a path involves symlinks and whether they are safe.

    Returns True if the path is safe (not a symlink or symlink within expected dir).
    Returns False if the path is a potentially unsafe symlink.
    """
    path = Path(path)

    try:
        if path.is_symlink():
            target = path.resolve(strict=True)
            logger.warning(
                "Symlink detected: %s → %s",
                path,
                target,
            )
            return False
    except (OSError, ValueError):
        return False

    # Check parent directories for symlinks
    for parent in path.parents:
        try:
            if parent.is_symlink():
                logger.warning("Symlink in parent path: %s", parent)
                return False
        except (OSError, ValueError):
            return False

    return True


def validate_file_size(
    file_size: int,
    max_file_size_mb: int = MAX_STAGING_FILE_SIZE_MB,
) -> None:
    """Validate that a file does not exceed the maximum staging size.

    Raises:
        EnforcementError: If the file is too large.
    """
    max_bytes = max_file_size_mb * 1024 * 1024
    if file_size > max_bytes:
        raise EnforcementError(
            f"File size {file_size} bytes exceeds maximum "
            f"{max_file_size_mb} MB for staging",
            code=EnforcementErrorCode.FILE_TOO_LARGE,
        )


def validate_staging_capacity(
    staging_dir: Path,
    additional_bytes: int,
    max_total_mb: int = MAX_STAGING_TOTAL_SIZE_MB,
) -> None:
    """Validate that the staging directory has capacity for additional data.

    Raises:
        EnforcementError: If staging is full.
    """
    max_total_bytes = max_total_mb * 1024 * 1024
    current_total = 0

    try:
        if staging_dir.exists():
            for f in staging_dir.rglob("*"):
                if f.is_file():
                    current_total += f.stat().st_size
    except (OSError, PermissionError) as exc:
        logger.warning("Cannot calculate staging size: %s", exc)

    if current_total + additional_bytes > max_total_bytes:
        raise EnforcementError(
            f"Staging directory full: {current_total} bytes + {additional_bytes} "
            f"would exceed {max_total_mb} MB limit",
            code=EnforcementErrorCode.STAGING_FULL,
        )


def validate_destination_accessible(path: str | Path) -> bool:
    """Check if a destination path/directory is accessible for writing."""
    path = Path(path)

    # For file destinations, check the parent directory
    check_dir = path.parent if not path.is_dir() else path

    try:
        if not check_dir.exists():
            return False
        # Check write permission
        return os.access(str(check_dir), os.W_OK)
    except (OSError, PermissionError):
        return False


def set_restrictive_permissions(path: Path) -> None:
    """Set restrictive file/directory permissions (owner-only).

    On Windows this is best-effort since POSIX permissions are limited.
    """
    try:
        if os.name == "nt":
            # Windows: remove all access except owner
            import subprocess
            subprocess.run(
                ["icacls", str(path), "/inheritance:r", "/grant:r",
                 f"{os.getlogin()}:(F)"],
                capture_output=True,
                timeout=10,
            )
        else:
            # POSIX: owner read/write only
            if path.is_dir():
                path.chmod(stat.S_IRWXU)
            else:
                path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except Exception as exc:
        logger.warning("Could not set restrictive permissions on %s: %s", path, exc)
