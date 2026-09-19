"""Event deduplicator — filters rapid-fire duplicate events."""

import logging
import time
from collections import OrderedDict

from sentinel_agent.pipeline.models import EndpointEvent

logger = logging.getLogger(__name__)


class EventDeduplicator:
    """Filter duplicate events using a time-windowed LRU cache.

    Watchdog and similar OS monitors often fire multiple events for a
    single logical file operation. This class suppresses duplicates
    within a configurable TTL window.
    """

    def __init__(self, ttl_seconds: float = 2.0, max_size: int = 10000) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cache: OrderedDict[str, float] = OrderedDict()

    def _make_key(self, event: EndpointEvent) -> str:
        """Create a dedup key from event attributes."""
        return f"{event.event_type}:{event.file_path}:{event.action}"

    def is_duplicate(self, event: EndpointEvent) -> bool:
        """Check if the event is a duplicate within the TTL window.

        Returns:
            True if the event should be suppressed as a duplicate.
        """
        now = time.monotonic()
        key = self._make_key(event)

        # Evict expired entries lazily
        self._evict_expired(now)

        if key in self._cache:
            last_seen = self._cache[key]
            if now - last_seen < self._ttl:
                logger.debug("Duplicate event suppressed: %s", key)
                return True
            # Update timestamp
            self._cache.move_to_end(key)
            self._cache[key] = now
            return False

        # New event
        self._cache[key] = now

        # Enforce max size
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

        return False

    def _evict_expired(self, now: float) -> None:
        """Remove entries older than TTL from the front of the cache."""
        cutoff = now - self._ttl
        while self._cache:
            # Peek at the oldest entry
            oldest_key = next(iter(self._cache))
            if self._cache[oldest_key] < cutoff:
                self._cache.popitem(last=False)
            else:
                break

    def clear(self) -> None:
        """Clear the dedup cache."""
        self._cache.clear()
