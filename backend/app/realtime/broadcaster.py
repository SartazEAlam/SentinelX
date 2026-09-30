"""WebSocket event broadcaster for real-time dashboard updates.

Publishes events to all connected, authenticated administrator sessions.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class EventBroadcaster:
    """Central broadcaster for real-time dashboard events.

    Maintains a set of connected WebSocket clients and publishes
    typed events to all authenticated sessions.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        logger.info(
            "WebSocket client connected. Total: %d",
            len(self._connections),
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info(
            "WebSocket client disconnected. Total: %d",
            len(self._connections),
        )

    async def publish(self, event_type: str, data: dict) -> None:
        """Broadcast an event to all connected clients."""
        message = json.dumps(
            {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        dead: list[WebSocket] = []
        async with self._lock:
            connections = list(self._connections)

        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def connection_count(self) -> int:
        """Number of active WebSocket connections."""
        return len(self._connections)


# Singleton instance
broadcaster = EventBroadcaster()
