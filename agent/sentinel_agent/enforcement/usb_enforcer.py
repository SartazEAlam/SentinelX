"""USB enforcer — operation-level USB protection.

Does NOT disable USB devices globally. Instead, intercepts specific file
transfer operations targeting removable media and applies enforcement
decisions on a per-operation basis.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sentinel_agent.enforcement.destination_detector import DestinationDetector, DestinationInfo
from sentinel_agent.enforcement.models import DestinationType

logger = logging.getLogger(__name__)


class USBEnforcer:
    """Operation-level USB enforcement.

    Evaluates file transfers targeting USB/removable destinations.
    Does NOT disable keyboard, mouse, webcam, or unrelated USB hardware.
    """

    def __init__(self, destination_detector: DestinationDetector) -> None:
        self._detector = destination_detector

    def classify_usb_destination(self, destination: str) -> DestinationInfo:
        """Classify a USB destination for enforcement purposes."""
        return self._detector.detect(destination)

    def is_usb_operation(self, destination: str) -> bool:
        """Check if an operation targets a USB/removable device."""
        info = self._detector.detect(destination)
        return info.destination_type in (
            DestinationType.USB_TRUSTED,
            DestinationType.USB_UNTRUSTED,
        )

    def is_usb_available(self, destination: str) -> bool:
        """Check if the USB device at the destination is still connected."""
        dest_path = Path(destination)
        try:
            # Check if the mount point exists and is accessible
            if dest_path.exists():
                return True
            # Check parent (mount point) accessibility
            mount = dest_path.parent
            while not mount.exists() and mount != mount.parent:
                mount = mount.parent
            return mount.exists() and mount != mount.parent
        except (OSError, PermissionError):
            return False

    def get_device_info(self, destination: str) -> dict:
        """Get information about the USB device at the destination."""
        info = self._detector.detect(destination)
        return info.to_dict()
