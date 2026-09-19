"""Tests for local SQLite event store."""

from pathlib import Path

import pytest
from sentinel_agent.storage.event_store import LocalEventStore


class TestLocalEventStore:
    """Tests for LocalEventStore."""

    @pytest.mark.asyncio
    async def test_init_creates_db(self, tmp_path: Path) -> None:
        """init_db creates the database file."""
        db_path = tmp_path / "test_events.db"
        store = LocalEventStore(db_path)
        await store.init_db()

        assert db_path.exists()
        await store.close()

    @pytest.mark.asyncio
    async def test_store_and_retrieve_event(self, tmp_path: Path) -> None:
        """Event can be stored and retrieved as pending."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        event = {"event_id": "evt-1", "event_type": "FILE_ACCESS", "action": "created"}
        await store.store_event(event)

        pending = await store.get_pending_events()
        assert len(pending) == 1
        row_id, data = pending[0]
        assert data["event_id"] == "evt-1"
        assert row_id == 1

        await store.close()

    @pytest.mark.asyncio
    async def test_store_multiple_events(self, tmp_path: Path) -> None:
        """Batch store works correctly."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        events = [
            {"event_id": f"evt-{i}", "event_type": "FILE_ACCESS"}
            for i in range(5)
        ]
        await store.store_events(events)

        pending = await store.get_pending_events()
        assert len(pending) == 5

        await store.close()

    @pytest.mark.asyncio
    async def test_mark_sent(self, tmp_path: Path) -> None:
        """Marking events as sent removes them from pending."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        await store.store_event({"event_id": "evt-1"})
        await store.store_event({"event_id": "evt-2"})

        pending = await store.get_pending_events()
        assert len(pending) == 2

        await store.mark_sent([pending[0][0]])

        pending_after = await store.get_pending_events()
        assert len(pending_after) == 1
        assert pending_after[0][1]["event_id"] == "evt-2"

        await store.close()

    @pytest.mark.asyncio
    async def test_mark_failed(self, tmp_path: Path) -> None:
        """Failed events are excluded from pending."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        await store.store_event({"event_id": "evt-1"})
        pending = await store.get_pending_events()
        await store.mark_failed([pending[0][0]])

        pending_after = await store.get_pending_events()
        assert len(pending_after) == 0

        await store.close()

    @pytest.mark.asyncio
    async def test_get_stats(self, tmp_path: Path) -> None:
        """Stats returns count by status."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        await store.store_events([{"event_id": f"evt-{i}"} for i in range(3)])
        pending = await store.get_pending_events()
        await store.mark_sent([pending[0][0]])

        stats = await store.get_stats()
        assert stats.get("PENDING", 0) == 2
        assert stats.get("SENT", 0) == 1

        await store.close()

    @pytest.mark.asyncio
    async def test_pending_count(self, tmp_path: Path) -> None:
        """pending_count returns correct count."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        assert await store.pending_count() == 0

        await store.store_events([{"event_id": f"evt-{i}"} for i in range(4)])
        assert await store.pending_count() == 4

        await store.close()

    @pytest.mark.asyncio
    async def test_get_pending_with_limit(self, tmp_path: Path) -> None:
        """get_pending_events respects the limit parameter."""
        store = LocalEventStore(tmp_path / "test.db")
        await store.init_db()

        await store.store_events([{"event_id": f"evt-{i}"} for i in range(10)])

        pending = await store.get_pending_events(limit=3)
        assert len(pending) == 3

        await store.close()
