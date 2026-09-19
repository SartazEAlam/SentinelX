"""Tests for the filesystem collector."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sentinel_agent.monitoring.filesystem import FileSystemCollector, SentinelXFileHandler
from sentinel_agent.pipeline.deduplicator import EventDeduplicator
from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue


class TestFileSystemCollector:
    """Tests for FileSystemCollector."""

    @pytest.mark.asyncio
    async def test_start_stop(self, tmp_path: Path) -> None:
        """Collector starts and stops cleanly."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        queue = EventQueue()
        normalizer = EventNormalizer(hash_enabled=False)
        dedup = EventDeduplicator()

        collector = FileSystemCollector(
            paths=[watch_dir],
            event_queue=queue,
            normalizer=normalizer,
            deduplicator=dedup,
        )

        await collector.start()
        assert collector.is_active()

        await collector.stop()
        assert not collector.is_active()

    @pytest.mark.asyncio
    async def test_no_paths_skips_start(self) -> None:
        """Collector with no paths doesn't start an observer."""
        queue = EventQueue()
        normalizer = EventNormalizer(hash_enabled=False)
        dedup = EventDeduplicator()

        collector = FileSystemCollector(
            paths=[],
            event_queue=queue,
            normalizer=normalizer,
            deduplicator=dedup,
        )

        await collector.start()
        assert not collector.is_active()

    @pytest.mark.asyncio
    async def test_nonexistent_path_warning(self, tmp_path: Path) -> None:
        """Non-existent paths are skipped with warning."""
        queue = EventQueue()
        normalizer = EventNormalizer(hash_enabled=False)
        dedup = EventDeduplicator()

        collector = FileSystemCollector(
            paths=[tmp_path / "nonexistent"],
            event_queue=queue,
            normalizer=normalizer,
            deduplicator=dedup,
        )

        await collector.start()
        # Observer might start but with no scheduled watches
        await collector.stop()

    @pytest.mark.asyncio
    async def test_file_creation_generates_event(self, tmp_path: Path) -> None:
        """Creating a file in a watched directory generates an event."""
        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        queue = EventQueue()
        normalizer = EventNormalizer(hash_enabled=False)
        dedup = EventDeduplicator()

        collector = FileSystemCollector(
            paths=[watch_dir],
            event_queue=queue,
            normalizer=normalizer,
            deduplicator=dedup,
        )

        await collector.start()

        # Create a file
        (watch_dir / "test.txt").write_text("hello")

        # Wait for watchdog to detect it
        await asyncio.sleep(1.0)

        await collector.stop()

        # Should have at least one event
        events = await queue.drain(max_count=100)
        assert len(events) >= 1

        # Check event properties
        event = events[0]
        assert event.event_type in ("FILE_ACCESS", "FILE_MOVE")
        assert "test.txt" in event.file_name


class TestSentinelXFileHandler:
    """Tests for file event filtering."""

    def test_should_ignore_excluded_extension(self) -> None:
        """Files with excluded extensions are ignored."""
        loop = asyncio.new_event_loop()
        handler = SentinelXFileHandler(
            event_queue=MagicMock(),
            normalizer=MagicMock(),
            deduplicator=MagicMock(),
            excluded_extensions={".tmp", ".log"},
            excluded_directories=set(),
            loop=loop,
        )

        assert handler._should_ignore("/path/to/file.tmp")
        assert handler._should_ignore("/path/to/debug.log")
        assert not handler._should_ignore("/path/to/data.txt")
        loop.close()

    def test_should_ignore_excluded_directory(self) -> None:
        """Files within excluded directories are ignored."""
        loop = asyncio.new_event_loop()
        handler = SentinelXFileHandler(
            event_queue=MagicMock(),
            normalizer=MagicMock(),
            deduplicator=MagicMock(),
            excluded_extensions=set(),
            excluded_directories={".git", "node_modules"},
            loop=loop,
        )

        assert handler._should_ignore("/project/.git/config")
        assert handler._should_ignore("/project/node_modules/pkg/index.js")
        assert not handler._should_ignore("/project/src/main.py")
        loop.close()
