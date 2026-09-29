"""External transfer enforcer — controlled network/cloud transfers.

For the prototype, this handles simulated cloud/network transfers
to demonstrate prevention without needing a full proxy architecture.
"""

from __future__ import annotations

import logging
from pathlib import Path

from sentinel_agent.enforcement.destination_detector import DestinationDetector, DestinationInfo
from sentinel_agent.enforcement.models import Decision, DestinationType, EnforcementResult

logger = logging.getLogger(__name__)


class ExternalTransferEnforcer:
    """Enforcement for network and cloud destination transfers.

    Focuses on operation-level prevention of specific transfers rather
    than universal arbitrary network interception.
    """

    def __init__(self, destination_detector: DestinationDetector) -> None:
        self._detector = destination_detector

    def is_external_transfer(self, destination: str) -> bool:
        """Check if an operation targets a network/cloud destination."""
        info = self._detector.detect(destination)
        return info.destination_type in (
            DestinationType.NETWORK_TRUSTED,
            DestinationType.NETWORK_UNTRUSTED,
            DestinationType.CLOUD,
        )

    def classify_destination(self, destination: str) -> DestinationInfo:
        """Classify a network/cloud destination."""
        return self._detector.detect(destination)

    def is_cloud_sync_folder(self, destination: str) -> bool:
        """Check if a path is inside a known cloud synchronization folder."""
        info = self._detector.detect(destination)
        return info.destination_type == DestinationType.CLOUD
