"""Filesystem collector — watchdog-based file event monitoring."""

import asyncio
import logging
from pathlib import Path
from typing import Any

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from sentinel_agent.pipeline.deduplicator import EventDeduplicator
from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue

logger = logging.getLogger(__name__)

# Map watchdog event types to SentinelX EventType values
WATCHDOG_TO_EVENT_TYPE = {
    "created": "FILE_ACCESS",
    "modified": "FILE_ACCESS",
    "deleted": "FILE_ACCESS",
    "moved": "FILE_MOVE",
}

WATCHDOG_TO_ACTION = {
    "created": "file_created",
    "modified": "file_modified",
    "deleted": "file_deleted",
    "moved": "file_moved",
}


class SentinelXFileHandler(FileSystemEventHandler):
    """Watchdog event handler that normalises and queues filesystem events."""

    def __init__(
        self,
        event_queue: EventQueue,
        normalizer: EventNormalizer,
        deduplicator: EventDeduplicator,
        excluded_extensions: set[str],
        excluded_directories: set[str],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__()
        self._queue = event_queue
        self._normalizer = normalizer
        self._dedup = deduplicator
        self._excluded_ext = excluded_extensions
        self._excluded_dirs = excluded_directories
        self._loop = loop

    def _should_ignore(self, path: str) -> bool:
        """Check if the path should be excluded from monitoring."""
        p = Path(path)

        # Check excluded extensions
        if p.suffix.lower() in self._excluded_ext:
            return True

        # Check excluded directories in the path
        parts = p.parts
        for part in parts:
            if part in self._excluded_dirs:
                return True

        return False

    def _handle_event(self, event: FileSystemEvent, event_kind: str) -> None:
        """Process a watchdog event into the pipeline."""
        if event.is_directory:
            return

        src_path = str(event.src_path)
        if self._should_ignore(src_path):
            return

        dest_path = ""
        if isinstance(event, FileMovedEvent):
            dest_path = str(event.dest_path)
            if self._should_ignore(dest_path):
                return

        event_type = WATCHDOG_TO_EVENT_TYPE.get(event_kind, "OTHER")
        action = WATCHDOG_TO_ACTION.get(event_kind, event_kind)

        endpoint_event = self._normalizer.normalize_fs_event(
            event_type=event_type,
            action=action,
            src_path=src_path,
            dest_path=dest_path,
        )

        if self._dedup.is_duplicate(endpoint_event):
            return

        # Schedule async put from the watchdog thread
        asyncio.run_coroutine_threadsafe(self._queue.put(endpoint_event), self._loop)
        logger.debug("FS event queued: %s %s", action, src_path)

    def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
        """Handle file creation."""
        self._handle_event(event, "created")

    def on_modified(self, event: FileModifiedEvent) -> None:  # type: ignore[override]
        """Handle file modification."""
        self._handle_event(event, "modified")

    def on_deleted(self, event: FileDeletedEvent) -> None:  # type: ignore[override]
        """Handle file deletion."""
        self._handle_event(event, "deleted")

    def on_moved(self, event: FileMovedEvent) -> None:  # type: ignore[override]
        """Handle file move/rename."""
        self._handle_event(event, "moved")


class FileSystemCollector:
    """Monitors configured directories for file system activity.

    Uses the watchdog library to observe file creates, modifies, deletes,
    and moves. Events are normalised, deduplicated, and pushed to the
    event queue for dispatch.
    """

    def __init__(
        self,
        paths: list[Path],
        event_queue: EventQueue,
        normalizer: EventNormalizer,
        deduplicator: EventDeduplicator,
        excluded_extensions: set[str] | None = None,
        excluded_directories: set[str] | None = None,
    ) -> None:
        self._paths = paths
        self._queue = event_queue
        self._normalizer = normalizer
        self._dedup = deduplicator
        self._excluded_ext = excluded_extensions or set()
        self._excluded_dirs = excluded_directories or set()
        self._observer: Any = None

    async def start(self) -> None:
        """Start the filesystem observer."""
        if not self._paths:
            logger.warning("No protected paths configured — filesystem monitoring disabled")
            return

        loop = asyncio.get_running_loop()
        handler = SentinelXFileHandler(
            event_queue=self._queue,
            normalizer=self._normalizer,
            deduplicator=self._dedup,
            excluded_extensions=self._excluded_ext,
            excluded_directories=self._excluded_dirs,
            loop=loop,
        )

        self._observer = Observer()
        for path in self._paths:
            if path.exists() and path.is_dir():
                self._observer.schedule(handler, str(path), recursive=True)
                logger.info("Monitoring filesystem path: %s", path)
            else:
                logger.warning("Skipping non-existent path: %s", path)

        self._observer.start()
        logger.info("Filesystem collector started (%d paths)", len(self._paths))

    async def stop(self) -> None:
        """Stop the filesystem observer."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("Filesystem collector stopped")

    def is_active(self) -> bool:
        """Check if the observer is running."""
        return self._observer is not None and self._observer.is_alive()
