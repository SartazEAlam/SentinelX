"""Event dispatcher — batches and sends events to the backend."""

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel_agent.pipeline.queue import EventQueue
    from sentinel_agent.storage.event_store import LocalEventStore
    from sentinel_agent.transport.http_transport import HTTPTransport

logger = logging.getLogger(__name__)


class EventDispatcher:
    """Background task that drains the event queue and sends batches.

    Responsibilities:
    - Periodically drain the queue and batch-send to the backend
    - On send failure, persist events to the local store
    - Periodically retry sending events from the local store
    """

    def __init__(
        self,
        queue: "EventQueue",
        transport: "HTTPTransport",
        store: "LocalEventStore",
        batch_size: int = 50,
        flush_interval: float = 10.0,
    ) -> None:
        self._queue = queue
        self._transport = transport
        self._store = store
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._task: asyncio.Task[None] | None = None
        self._running = False

        # Metrics
        self.events_sent: int = 0
        self.events_failed: int = 0
        self.batches_sent: int = 0

    @property
    def is_running(self) -> bool:
        """Whether the dispatcher loop is active."""
        return self._running

    async def start(self) -> None:
        """Start the dispatcher background loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Event dispatcher started (batch_size=%d, interval=%.1fs)",
            self._batch_size,
            self._flush_interval,
        )

    async def stop(self) -> None:
        """Stop the dispatcher, flushing any remaining events."""
        if not self._running:
            return
        self._running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        # Final flush
        await self._flush_queue()
        await self._retry_local_store()
        logger.info(
            "Dispatcher stopped — sent=%d, failed=%d, batches=%d",
            self.events_sent,
            self.events_failed,
            self.batches_sent,
        )

    async def _run_loop(self) -> None:
        """Main dispatcher loop."""
        retry_counter = 0

        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)

                # Flush queue to backend
                await self._flush_queue()

                # Every 6th cycle (~60s), retry from local store
                retry_counter += 1
                if retry_counter >= 6:
                    await self._retry_local_store()
                    retry_counter = 0

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Dispatcher loop error: %s", exc)

    async def _flush_queue(self) -> None:
        """Drain the queue and send events in batches."""
        while not self._queue.is_empty:
            events = await self._queue.drain(self._batch_size)
            if not events:
                break

            api_dicts = [e.to_api_dict() for e in events]
            count = len(api_dicts)

            if count == 1:
                result = await self._transport.send_event(api_dicts[0])
            else:
                result = await self._transport.send_events_batch(api_dicts)

            if result.success:
                self.events_sent += count
                self.batches_sent += 1
                logger.debug("Sent %d events to backend", count)
            else:
                logger.warning(
                    "Failed to send %d events — storing locally: %s",
                    count,
                    result.error,
                )
                self.events_failed += count
                await self._store.store_events(api_dicts)

    async def _retry_local_store(self) -> None:
        """Retry sending events from the local store."""
        pending = await self._store.get_pending_events(limit=self._batch_size)
        if not pending:
            return

        ids = [row_id for row_id, _ in pending]
        events = [event_data for _, event_data in pending]

        logger.info("Retrying %d events from local store", len(events))

        if len(events) == 1:
            result = await self._transport.send_event(events[0])
        else:
            result = await self._transport.send_events_batch(events)

        if result.success:
            await self._store.mark_sent(ids)
            self.events_sent += len(events)
            logger.info("Retried and sent %d events from local store", len(events))
        else:
            logger.warning("Retry failed for %d events: %s", len(events), result.error)
