"""Async event queue — bridges collectors and the dispatcher."""

import asyncio
import logging

from sentinel_agent.pipeline.models import EndpointEvent

logger = logging.getLogger(__name__)


class EventQueue:
    """Thread-safe async queue bridging collectors and the dispatcher.

    Collectors push events in, the dispatcher drains them out in batches.
    """

    def __init__(self, max_size: int = 5000) -> None:
        self._queue: asyncio.Queue[EndpointEvent] = asyncio.Queue(maxsize=max_size)

    async def put(self, event: EndpointEvent) -> None:
        """Enqueue an event. Drops if the queue is full."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full — dropping event %s", event.event_id)

    async def drain(self, max_count: int = 50) -> list[EndpointEvent]:
        """Dequeue up to ``max_count`` events without blocking.

        Returns:
            List of events drained from the queue.
        """
        events: list[EndpointEvent] = []
        for _ in range(max_count):
            try:
                event = self._queue.get_nowait()
                events.append(event)
            except asyncio.QueueEmpty:
                break
        return events

    @property
    def size(self) -> int:
        """Current number of events in the queue."""
        return self._queue.qsize()

    @property
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()
