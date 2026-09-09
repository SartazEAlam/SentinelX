"""File system and endpoint monitoring.

Future implementations:
    - FileSystemMonitor: watchdog-based file event observer
    - USBMonitor: USB device attach/detach detection
    - ProcessMonitor: process activity tracking
"""

from abc import ABC, abstractmethod


class BaseMonitor(ABC):
    """Abstract base for all monitoring modules."""

    @abstractmethod
    async def start(self) -> None:
        """Start monitoring."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop monitoring and release resources."""
        ...

    @abstractmethod
    def is_active(self) -> bool:
        """Check if the monitor is currently active."""
        ...
