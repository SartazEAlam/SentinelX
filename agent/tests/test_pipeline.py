"""Tests for the event pipeline — models, normalizer, deduplicator, queue."""

import time
from pathlib import Path

import pytest
from sentinel_agent.pipeline.deduplicator import EventDeduplicator
from sentinel_agent.pipeline.models import EndpointEvent
from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue


class TestEndpointEvent:
    """Tests for the EndpointEvent model."""

    def test_auto_generates_id(self) -> None:
        """Event gets a UUID event_id automatically."""
        event = EndpointEvent(event_type="FILE_ACCESS")
        assert event.event_id != ""
        assert len(event.event_id) == 36  # UUID format

    def test_to_api_dict_minimal(self) -> None:
        """to_api_dict produces required fields only."""
        event = EndpointEvent(event_type="FILE_ACCESS")
        d = event.to_api_dict()
        assert d["event_id"] == event.event_id
        assert d["event_type"] == "FILE_ACCESS"
        assert "timestamp" in d
        # Optional fields with empty strings should be omitted
        assert "source" not in d
        assert "file_name" not in d

    def test_to_api_dict_full(self) -> None:
        """to_api_dict includes all populated optional fields."""
        event = EndpointEvent(
            event_type="FILE_COPY",
            action="file_copied",
            source="/src/file.txt",
            destination="/dst/file.txt",
            file_name="file.txt",
            file_path="/src/file.txt",
            file_size=1024,
            file_hash="abc123",
            process_name="python",
            process_id=12345,
            user_context="testuser",
            metadata={"key": "value"},
        )
        d = event.to_api_dict()
        assert d["action"] == "file_copied"
        assert d["source"] == "/src/file.txt"
        assert d["destination"] == "/dst/file.txt"
        assert d["file_size"] == 1024
        assert d["file_hash"] == "abc123"
        assert d["process_name"] == "python"
        assert d["process_id"] == 12345
        assert d["metadata_json"] == {"key": "value"}


class TestEventNormalizer:
    """Tests for EventNormalizer."""

    def test_normalize_fs_event(self, tmp_path: Path) -> None:
        """Filesystem event normalisation includes file info."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        normalizer = EventNormalizer(hash_enabled=True, hash_max_bytes=1024 * 1024)
        event = normalizer.normalize_fs_event(
            event_type="FILE_ACCESS",
            action="file_created",
            src_path=str(test_file),
        )

        assert event.event_type == "FILE_ACCESS"
        assert event.action == "file_created"
        assert event.file_name == "test.txt"
        assert event.file_size == 11
        assert event.file_hash != ""  # SHA-256 hash

    def test_normalize_fs_event_nonexistent_file(self) -> None:
        """Non-existent file gets no size or hash."""
        normalizer = EventNormalizer()
        event = normalizer.normalize_fs_event(
            event_type="FILE_ACCESS",
            action="file_deleted",
            src_path="/nonexistent/path.txt",
        )
        assert event.file_size is None
        assert event.file_hash is None

    def test_normalize_fs_event_hash_disabled(self, tmp_path: Path) -> None:
        """Hash is skipped when disabled."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        normalizer = EventNormalizer(hash_enabled=False)
        event = normalizer.normalize_fs_event(
            event_type="FILE_ACCESS",
            action="file_created",
            src_path=str(test_file),
        )
        assert event.file_hash is None

    def test_normalize_usb_event(self) -> None:
        """USB event normalisation."""
        normalizer = EventNormalizer()
        event = normalizer.normalize_usb_event(
            action="usb_connected",
            device_path="/dev/sdb1",
            mountpoint="/media/usb",
            fstype="vfat",
        )
        assert event.event_type == "USB_ACTIVITY"
        assert event.action == "usb_connected"
        assert event.metadata["fstype"] == "vfat"

    def test_normalize_process_event(self) -> None:
        """Process event normalisation."""
        normalizer = EventNormalizer()
        event = normalizer.normalize_process_event(
            action="process_started",
            process_name="python",
            process_id=12345,
            details={"cmdline": "python script.py"},
        )
        assert event.event_type == "PROCESS_ACTIVITY"
        assert event.process_id == 12345


class TestEventDeduplicator:
    """Tests for EventDeduplicator."""

    def test_first_event_not_duplicate(self) -> None:
        """First event is never a duplicate."""
        dedup = EventDeduplicator(ttl_seconds=2.0)
        event = EndpointEvent(event_type="FILE_ACCESS", file_path="/a.txt", action="created")
        assert not dedup.is_duplicate(event)

    def test_same_event_within_ttl_is_duplicate(self) -> None:
        """Same event within TTL window is duplicate."""
        dedup = EventDeduplicator(ttl_seconds=5.0)
        event = EndpointEvent(event_type="FILE_ACCESS", file_path="/a.txt", action="created")
        assert not dedup.is_duplicate(event)
        assert dedup.is_duplicate(event)  # Duplicate within window

    def test_different_events_not_duplicate(self) -> None:
        """Different events are not duplicates of each other."""
        dedup = EventDeduplicator(ttl_seconds=5.0)
        e1 = EndpointEvent(event_type="FILE_ACCESS", file_path="/a.txt", action="created")
        e2 = EndpointEvent(event_type="FILE_ACCESS", file_path="/b.txt", action="created")
        assert not dedup.is_duplicate(e1)
        assert not dedup.is_duplicate(e2)

    def test_event_after_ttl_not_duplicate(self) -> None:
        """Same event after TTL window expires is not a duplicate."""
        dedup = EventDeduplicator(ttl_seconds=0.05)  # 50ms TTL
        event = EndpointEvent(event_type="FILE_ACCESS", file_path="/a.txt", action="created")
        assert not dedup.is_duplicate(event)
        time.sleep(0.1)  # Wait for TTL to expire
        assert not dedup.is_duplicate(event)

    def test_clear(self) -> None:
        """Clear resets the cache."""
        dedup = EventDeduplicator(ttl_seconds=60.0)
        event = EndpointEvent(event_type="FILE_ACCESS", file_path="/a.txt", action="created")
        dedup.is_duplicate(event)
        dedup.clear()
        assert not dedup.is_duplicate(event)


class TestEventQueue:
    """Tests for EventQueue."""

    @pytest.mark.asyncio
    async def test_put_and_drain(self) -> None:
        """Events can be put and drained."""
        queue = EventQueue(max_size=100)
        e1 = EndpointEvent(event_type="FILE_ACCESS")
        e2 = EndpointEvent(event_type="USB_ACTIVITY")

        await queue.put(e1)
        await queue.put(e2)
        assert queue.size == 2

        drained = await queue.drain(max_count=10)
        assert len(drained) == 2
        assert queue.size == 0

    @pytest.mark.asyncio
    async def test_drain_respects_max_count(self) -> None:
        """Drain returns at most max_count items."""
        queue = EventQueue(max_size=100)
        for _ in range(5):
            await queue.put(EndpointEvent(event_type="FILE_ACCESS"))

        drained = await queue.drain(max_count=3)
        assert len(drained) == 3
        assert queue.size == 2

    @pytest.mark.asyncio
    async def test_drain_empty_queue(self) -> None:
        """Draining an empty queue returns empty list."""
        queue = EventQueue()
        drained = await queue.drain()
        assert drained == []

    @pytest.mark.asyncio
    async def test_is_empty(self) -> None:
        """is_empty reflects queue state."""
        queue = EventQueue()
        assert queue.is_empty
        await queue.put(EndpointEvent(event_type="FILE_ACCESS"))
        assert not queue.is_empty
