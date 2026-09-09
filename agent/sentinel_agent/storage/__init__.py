"""Local event storage and persistence.

Future implementations:
    - LocalStore: SQLite-based local event cache
    - EventQueue: queue for events pending transmission
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseStorage(ABC):
    """Abstract base for local event storage."""

    @abstractmethod
    def store_event(self, event: dict[str, Any]) -> None:
        """Persist an event locally.

        Args:
            event: Event data to store.
        """
        ...

    @abstractmethod
    def get_pending_events(self) -> list[dict[str, Any]]:
        """Retrieve events pending transmission.

        Returns:
            List of pending event dictionaries.
        """
        ...
