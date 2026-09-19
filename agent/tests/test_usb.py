"""Tests for the USB collector."""

from unittest.mock import MagicMock, patch

import pytest
from sentinel_agent.monitoring.usb import USBCollector, _get_removable_partitions
from sentinel_agent.pipeline.normalizer import EventNormalizer
from sentinel_agent.pipeline.queue import EventQueue


class TestGetRemovablePartitions:
    """Tests for removable partition detection."""

    @patch("sentinel_agent.monitoring.usb.psutil")
    def test_detects_removable(self, mock_psutil: MagicMock) -> None:
        """Removable partitions are detected."""
        mock_part = MagicMock()
        mock_part.device = "E:\\"
        mock_part.mountpoint = "E:\\"
        mock_part.fstype = "FAT32"
        mock_part.opts = "rw,removable"

        mock_psutil.disk_partitions.return_value = [mock_part]

        result = _get_removable_partitions()
        assert "E:\\" in result
        assert result["E:\\"]["fstype"] == "FAT32"

    @patch("sentinel_agent.monitoring.usb.psutil")
    def test_ignores_fixed_disks(self, mock_psutil: MagicMock) -> None:
        """Fixed disks are not included."""
        mock_part = MagicMock()
        mock_part.device = "C:\\"
        mock_part.mountpoint = "C:\\"
        mock_part.fstype = "NTFS"
        mock_part.opts = "rw,fixed"

        mock_psutil.disk_partitions.return_value = [mock_part]

        result = _get_removable_partitions()
        assert len(result) == 0


class TestUSBCollector:
    """Tests for USBCollector."""

    @pytest.mark.asyncio
    async def test_start_stop(self) -> None:
        """USB collector starts and stops cleanly."""
        queue = EventQueue()
        normalizer = EventNormalizer()

        collector = USBCollector(
            event_queue=queue,
            normalizer=normalizer,
            poll_interval=1,
        )

        await collector.start()
        assert collector.is_active()

        await collector.stop()
        assert not collector.is_active()

    @pytest.mark.asyncio
    async def test_detect_new_device(self) -> None:
        """New USB device triggers an event."""
        queue = EventQueue()
        normalizer = EventNormalizer()

        collector = USBCollector(
            event_queue=queue,
            normalizer=normalizer,
            poll_interval=1,
        )
        # Set known state as empty
        collector._known_devices = {}

        # Mock detection of a new device
        with patch("sentinel_agent.monitoring.usb._get_removable_partitions") as mock_get:
            mock_get.return_value = {
                "E:\\": {"mountpoint": "E:\\", "fstype": "FAT32"}
            }
            await collector._check_devices()

        events = await queue.drain(max_count=10)
        assert len(events) == 1
        assert events[0].event_type == "USB_ACTIVITY"
        assert events[0].action == "usb_connected"

    @pytest.mark.asyncio
    async def test_detect_removed_device(self) -> None:
        """Removed USB device triggers a disconnection event."""
        queue = EventQueue()
        normalizer = EventNormalizer()

        collector = USBCollector(
            event_queue=queue,
            normalizer=normalizer,
            poll_interval=1,
        )
        # Set known state with a device
        collector._known_devices = {
            "E:\\": {"mountpoint": "E:\\", "fstype": "FAT32"}
        }

        # Mock: device gone
        with patch("sentinel_agent.monitoring.usb._get_removable_partitions") as mock_get:
            mock_get.return_value = {}
            await collector._check_devices()

        events = await queue.drain(max_count=10)
        assert len(events) == 1
        assert events[0].action == "usb_disconnected"
