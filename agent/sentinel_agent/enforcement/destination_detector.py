"""Destination detector — classifies where an operation is targeting.

Determines destination type from path, OS metadata, and configuration.
"""

from __future__ import annotations

import logging
import os
import platform
from pathlib import Path

import psutil

from sentinel_agent.enforcement.models import DestinationType

logger = logging.getLogger(__name__)


class DestinationInfo:
    """Structured information about an operation destination."""

    __slots__ = (
        "destination_type", "path", "mount_point", "device",
        "is_removable", "trust_status", "fs_type",
    )

    def __init__(
        self,
        destination_type: DestinationType = DestinationType.UNKNOWN,
        path: str = "",
        mount_point: str = "",
        device: str = "",
        is_removable: bool = False,
        trust_status: str = "UNKNOWN",
        fs_type: str = "",
    ) -> None:
        self.destination_type = destination_type
        self.path = path
        self.mount_point = mount_point
        self.device = device
        self.is_removable = is_removable
        self.trust_status = trust_status
        self.fs_type = fs_type

    def to_dict(self) -> dict:
        return {
            "destination_type": self.destination_type.value,
            "path": self.path,
            "mount_point": self.mount_point,
            "device": self.device,
            "is_removable": self.is_removable,
            "trust_status": self.trust_status,
            "fs_type": self.fs_type,
        }


class DestinationDetector:
    """Classifies operation destinations using OS metadata and configuration.

    Uses psutil partition data and configured trusted/untrusted paths
    to determine destination type and trust status.
    """

    def __init__(
        self,
        trusted_paths: list[Path] | None = None,
        trusted_hosts: list[str] | None = None,
    ) -> None:
        self._trusted_paths = [p.resolve() for p in (trusted_paths or [])]
        self._trusted_hosts = [h.lower() for h in (trusted_hosts or ["localhost", "127.0.0.1"])]
        self._removable_cache: dict[str, dict] | None = None

    def detect(self, destination: str) -> DestinationInfo:
        """Classify a destination path.

        Args:
            destination: The target path or URL.

        Returns:
            DestinationInfo with type and metadata.
        """
        if not destination:
            return DestinationInfo(destination_type=DestinationType.UNKNOWN)

        dest_lower = destination.lower().replace("\\", "/")

        # HTTP/HTTPS URLs → network/cloud
        if dest_lower.startswith(("http://", "https://")):
            return self._classify_url(destination)

        # UNC/network paths
        if dest_lower.startswith("//") or destination.startswith("\\\\"):
            return DestinationInfo(
                destination_type=DestinationType.NETWORK_UNTRUSTED,
                path=destination,
                trust_status="UNTRUSTED",
            )

        # Cloud sync folder markers
        cloud_markers = [
            "dropbox", "onedrive", "google drive", "gdrive",
            "icloud", "box sync", "mega",
        ]
        if any(marker in dest_lower for marker in cloud_markers):
            return DestinationInfo(
                destination_type=DestinationType.CLOUD,
                path=destination,
                trust_status="UNTRUSTED",
            )

        # File system path — check if it's on removable media
        try:
            dest_path = Path(destination).resolve()
        except (OSError, ValueError):
            return DestinationInfo(
                destination_type=DestinationType.UNKNOWN,
                path=destination,
            )

        # Check USB / removable
        removable_info = self._check_removable(str(dest_path))
        if removable_info is not None:
            is_trusted = self._is_trusted_path(dest_path)
            return DestinationInfo(
                destination_type=(
                    DestinationType.USB_TRUSTED if is_trusted
                    else DestinationType.USB_UNTRUSTED
                ),
                path=str(dest_path),
                mount_point=removable_info.get("mountpoint", ""),
                device=removable_info.get("device", ""),
                is_removable=True,
                trust_status="TRUSTED" if is_trusted else "UNTRUSTED",
                fs_type=removable_info.get("fstype", ""),
            )

        # Local path — check trust
        if self._is_trusted_path(dest_path):
            return DestinationInfo(
                destination_type=DestinationType.LOCAL_TRUSTED,
                path=str(dest_path),
                trust_status="TRUSTED",
            )

        return DestinationInfo(
            destination_type=DestinationType.LOCAL_UNTRUSTED,
            path=str(dest_path),
            trust_status="UNTRUSTED",
        )

    def _classify_url(self, url: str) -> DestinationInfo:
        """Classify an HTTP/HTTPS URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()

            is_trusted = hostname in self._trusted_hosts
            return DestinationInfo(
                destination_type=(
                    DestinationType.NETWORK_TRUSTED if is_trusted
                    else DestinationType.NETWORK_UNTRUSTED
                ),
                path=url,
                trust_status="TRUSTED" if is_trusted else "UNTRUSTED",
            )
        except Exception:
            return DestinationInfo(
                destination_type=DestinationType.NETWORK_UNTRUSTED,
                path=url,
                trust_status="UNTRUSTED",
            )

    def _check_removable(self, path: str) -> dict | None:
        """Check if a path is on removable/USB media using psutil."""
        # Refresh removable device cache
        self._refresh_removable_cache()
        if not self._removable_cache:
            return None

        # Normalize path for comparison
        path_lower = path.lower().replace("\\", "/")

        for device, info in self._removable_cache.items():
            mount = info["mountpoint"].lower().replace("\\", "/")
            if not mount.endswith("/"):
                mount += "/"
            if path_lower.startswith(mount) or path_lower == mount.rstrip("/"):
                return info

        # Windows: check drive letter heuristic for removable drives
        if platform.system() == "Windows" and len(path) >= 2 and path[1] == ":":
            drive = path[:2].upper()
            # E:, F:, G: etc. are commonly removable
            if drive[0] in "EFGHIJKLMNOPQRSTUVWXYZ":
                try:
                    import ctypes
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(f"{drive}\\")
                    # DRIVE_REMOVABLE = 2
                    if drive_type == 2:
                        return {
                            "mountpoint": f"{drive}\\",
                            "device": drive,
                            "fstype": "unknown",
                        }
                except Exception:
                    pass

        return None

    def _refresh_removable_cache(self) -> None:
        """Update the cache of removable/USB partitions."""
        try:
            removable: dict[str, dict] = {}
            for part in psutil.disk_partitions(all=False):
                opts = part.opts.lower()
                is_removable = (
                    "removable" in opts
                    or "cdrom" in opts
                    or part.mountpoint.startswith(("/media/", "/mnt/"))
                )
                if is_removable:
                    removable[part.device] = {
                        "mountpoint": part.mountpoint,
                        "device": part.device,
                        "fstype": part.fstype,
                    }
            self._removable_cache = removable
        except Exception as exc:
            logger.debug("Error refreshing removable cache: %s", exc)
            if self._removable_cache is None:
                self._removable_cache = {}

    def _is_trusted_path(self, path: Path) -> bool:
        """Check if a path is within a trusted directory."""
        resolved = path.resolve()
        for trusted in self._trusted_paths:
            try:
                resolved.relative_to(trusted)
                return True
            except ValueError:
                continue
        return False

    def is_usb_destination(self, destination: str) -> bool:
        """Quick check if a destination is on USB/removable media."""
        info = self.detect(destination)
        return info.destination_type in (
            DestinationType.USB_TRUSTED,
            DestinationType.USB_UNTRUSTED,
        )
