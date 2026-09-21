"""Event normaliser — converts raw collector output to EndpointEvent."""

import hashlib
import logging
from pathlib import Path
from typing import Any

from sentinel_agent.pipeline.models import EndpointEvent, get_current_user
from sentinel_agent.classification.engine import ClassificationEngine

logger = logging.getLogger(__name__)


class EventNormalizer:
    """Transforms raw OS-level events into normalised EndpointEvent objects.

    Enriches events with file metadata (size, hash) and user context.
    """

    def __init__(
        self,
        hash_enabled: bool = True,
        hash_max_bytes: int = 50 * 1024 * 1024,
        classification_engine: ClassificationEngine | None = None,
    ) -> None:
        self._hash_enabled = hash_enabled
        self._hash_max_bytes = hash_max_bytes
        self._classification_engine = classification_engine

    def normalize_fs_event(
        self,
        event_type: str,
        action: str,
        src_path: str,
        dest_path: str = "",
        process_name: str = "",
        process_id: int | None = None,
    ) -> EndpointEvent:
        """Normalise a filesystem event from watchdog."""
        path = Path(src_path)
        file_size: int | None = None
        file_hash: str | None = None

        # Get file metadata if the file still exists
        try:
            if path.exists() and path.is_file():
                file_size = path.stat().st_size
                if self._hash_enabled and file_size <= self._hash_max_bytes:
                    file_hash = self._compute_hash(path)
        except (OSError, PermissionError) as exc:
            logger.debug("Cannot stat file %s: %s", src_path, exc)

        event = EndpointEvent(
            event_type=event_type,
            action=action,
            source=src_path,
            destination=dest_path,
            file_name=path.name,
            file_path=str(path),
            file_size=file_size,
            file_hash=file_hash,
            process_name=process_name,
            process_id=process_id,
            user_context=get_current_user(),
        )
        
        # Classification
        if self._classification_engine and event.file_path and path.exists() and path.is_file():
            try:
                result = self._classification_engine.classify_file(path)
                event.classification = result
            except Exception as exc:
                logger.error("Classification failed for %s: %s", path, exc)
                
        return event

    def normalize_usb_event(
        self,
        action: str,
        device_path: str,
        mountpoint: str = "",
        fstype: str = "",
    ) -> EndpointEvent:
        """Normalise a USB device event."""
        return EndpointEvent(
            event_type="USB_ACTIVITY",
            action=action,
            source=device_path,
            destination=mountpoint,
            user_context=get_current_user(),
            metadata={
                "fstype": fstype,
                "mountpoint": mountpoint,
                "device": device_path,
            },
        )

    def normalize_process_event(
        self,
        action: str,
        process_name: str,
        process_id: int,
        details: dict[str, Any] | None = None,
    ) -> EndpointEvent:
        """Normalise a process-related event."""
        return EndpointEvent(
            event_type="PROCESS_ACTIVITY",
            action=action,
            process_name=process_name,
            process_id=process_id,
            user_context=get_current_user(),
            metadata=details or {},
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
        except (OSError, PermissionError) as exc:
            logger.debug("Cannot hash file %s: %s", path, exc)
            return ""
