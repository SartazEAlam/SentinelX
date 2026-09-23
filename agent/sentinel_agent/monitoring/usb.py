"""USB collector — removable media detection via psutil."""

import asyncio
import logging

import psutil

from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue

logger = logging.getLogger(__name__)


def _get_removable_partitions() -> dict[str, dict[str, str]]:
    """Detect removable/external partitions using psutil.

    Returns a dict keyed by device name with mountpoint and fstype.
    """
    removable: dict[str, dict[str, str]] = {}
    try:
        for part in psutil.disk_partitions(all=False):
            opts = part.opts.lower()
            # Windows: 'removable' in opts; Linux/macOS: check /media/, /mnt/, etc.
            is_removable = (
                "removable" in opts
                or "cdrom" in opts
                or part.mountpoint.startswith(("/media/", "/mnt/"))
            )
            if is_removable:
                removable[part.device] = {
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                }
    except Exception as exc:
        logger.debug("Error detecting partitions: %s", exc)
    return removable


class USBCollector:
    """Detects USB/removable media insertion and removal.

    Polls ``psutil.disk_partitions()`` at regular intervals and emits
    USB_ACTIVITY events when new removable drives appear or disappear.
    """

    def __init__(
        self,
        event_queue: EventQueue,
        normalizer: EventNormalizer,
        poll_interval: int = 5,
    ) -> None:
        self._queue = event_queue
        self._normalizer = normalizer
        self._poll_interval = poll_interval
        self._known_devices: dict[str, dict[str, str]] = {}
        self._task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        """Start USB polling."""
        if self._running:
            return
        self._running = True
        # Snapshot current removable devices
        self._known_devices = _get_removable_partitions()
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "USB collector started (poll_interval=%ds, known_devices=%d)",
            self._poll_interval,
            len(self._known_devices),
        )

    async def stop(self) -> None:
        """Stop USB polling."""
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
        logger.info("USB collector stopped")

    def is_active(self) -> bool:
        """Check if the polling loop is active."""
        return self._running

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                await self._check_devices()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("USB poll error: %s", exc)

    async def _check_devices(self) -> None:
        """Compare current removable devices against known state."""
        current = _get_removable_partitions()

        # Detect new devices
        for device, info in current.items():
            if device not in self._known_devices:
                logger.info("USB device connected: %s at %s", device, info["mountpoint"])
                event = self._normalizer.normalize_usb_event(
                    action="usb_connected",
                    device_path=device,
                    mountpoint=info["mountpoint"],
                    fstype=info["fstype"],
                )
                await self._queue.put(event)

        # Detect removed devices
        for device, info in self._known_devices.items():
            if device not in current:
                logger.info("USB device removed: %s", device)
                event = self._normalizer.normalize_usb_event(
                    action="usb_disconnected",
                    device_path=device,
                    mountpoint=info["mountpoint"],
                    fstype=info["fstype"],
                )
                await self._queue.put(event)

        self._known_devices = current
