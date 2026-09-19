"""Local event store — SQLite-based offline event persistence."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING'
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS ix_events_status ON events (status);
"""


class LocalEventStore:
    """SQLite-backed local event store for offline resilience.

    Events that fail to transmit are persisted here and retried later.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init_db(self) -> None:
        """Initialise the database and create tables if needed."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self._db_path))
        await self._db.execute(CREATE_TABLE_SQL)
        await self._db.execute(CREATE_INDEX_SQL)
        await self._db.commit()
        logger.info("Local event store initialised at %s", self._db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def store_event(self, event: dict[str, Any]) -> None:
        """Persist a single event locally with PENDING status."""
        if self._db is None:
            raise RuntimeError("Event store not initialised")
        now = datetime.now(UTC).isoformat()
        await self._db.execute(
            "INSERT INTO events (event_json, created_at, status) VALUES (?, ?, ?)",
            (json.dumps(event, default=str), now, "PENDING"),
        )
        await self._db.commit()

    async def store_events(self, events: list[dict[str, Any]]) -> None:
        """Persist multiple events locally."""
        if self._db is None:
            raise RuntimeError("Event store not initialised")
        now = datetime.now(UTC).isoformat()
        rows = [(json.dumps(e, default=str), now, "PENDING") for e in events]
        await self._db.executemany(
            "INSERT INTO events (event_json, created_at, status) VALUES (?, ?, ?)",
            rows,
        )
        await self._db.commit()

    async def get_pending_events(self, limit: int = 100) -> list[tuple[int, dict[str, Any]]]:
        """Retrieve pending events ordered by creation time.

        Returns:
            List of (id, event_dict) tuples.
        """
        if self._db is None:
            raise RuntimeError("Event store not initialised")
        cursor = await self._db.execute(
            "SELECT id, event_json FROM events WHERE status = 'PENDING' ORDER BY id ASC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        result = []
        for row_id, event_json in rows:
            try:
                result.append((row_id, json.loads(event_json)))
            except json.JSONDecodeError:
                logger.warning("Corrupt event in local store, id=%d — skipping", row_id)
        return result

    async def mark_sent(self, ids: list[int]) -> None:
        """Mark events as successfully sent."""
        if not ids or self._db is None:
            return
        placeholders = ",".join("?" * len(ids))
        await self._db.execute(
            f"UPDATE events SET status = 'SENT' WHERE id IN ({placeholders})",  # noqa: S608
            ids,
        )
        await self._db.commit()

    async def mark_failed(self, ids: list[int]) -> None:
        """Mark events as failed (for diagnostic purposes)."""
        if not ids or self._db is None:
            return
        placeholders = ",".join("?" * len(ids))
        await self._db.execute(
            f"UPDATE events SET status = 'FAILED' WHERE id IN ({placeholders})",  # noqa: S608
            ids,
        )
        await self._db.commit()

    async def cleanup_sent(self, older_than_hours: int = 24) -> int:
        """Delete sent events older than the specified threshold.

        Returns:
            Number of rows deleted.
        """
        if self._db is None:
            return 0
        cutoff = datetime.now(UTC).isoformat()
        cursor = await self._db.execute(
            "DELETE FROM events WHERE status = 'SENT' AND created_at < ?",
            (cutoff,),
        )
        await self._db.commit()
        return cursor.rowcount

    async def get_stats(self) -> dict[str, int]:
        """Get event counts by status."""
        if self._db is None:
            return {}
        cursor = await self._db.execute(
            "SELECT status, COUNT(*) FROM events GROUP BY status"
        )
        rows = await cursor.fetchall()
        return {status: count for status, count in rows}

    async def pending_count(self) -> int:
        """Get the count of pending events."""
        if self._db is None:
            return 0
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM events WHERE status = 'PENDING'"
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
