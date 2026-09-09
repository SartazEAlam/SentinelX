"""Server communication transport layer.

Future implementations:
    - HTTPTransport: HTTPS REST communication with the central server
    - EventBuffer: local buffering and retry for failed transmissions
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTransport(ABC):
    """Abstract base for agent-server communication."""

    @abstractmethod
    async def send_event(self, event: dict[str, Any]) -> bool:
        """Send a security event to the central server.

        Args:
            event: Event data to transmit.

        Returns:
            True if the event was sent successfully.
        """
        ...

    @abstractmethod
    async def fetch_policies(self) -> list[dict[str, Any]]:
        """Fetch current policies from the central server.

        Returns:
            List of policy dictionaries.
        """
        ...
