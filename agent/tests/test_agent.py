"""Tests for agent configuration and lifecycle."""

import asyncio

import pytest

from sentinel_agent.agent import SentinelAgent
from sentinel_agent.config import AgentSettings, MonitoringMode


class TestAgentConfig:
    """Tests for agent configuration."""

    def test_default_settings(self) -> None:
        """Agent settings load with safe defaults."""
        settings = AgentSettings()
        assert settings.DEVICE_ID == "dev-endpoint-001"
        assert settings.MONITORING_MODE == MonitoringMode.MONITOR_ONLY

    def test_monitoring_modes(self) -> None:
        """All monitoring modes are recognized."""
        for mode in MonitoringMode:
            settings = AgentSettings(MONITORING_MODE=mode)
            assert settings.MONITORING_MODE == mode

    def test_invalid_server_url_rejected(self) -> None:
        """Invalid server URL is rejected."""
        with pytest.raises(Exception):
            AgentSettings(SERVER_URL="not-a-url")

    def test_invalid_log_level_rejected(self) -> None:
        """Invalid log level is rejected."""
        with pytest.raises(Exception):
            AgentSettings(LOG_LEVEL="INVALID")

    def test_protected_paths_parsing(self) -> None:
        """Comma-separated protected paths are parsed correctly."""
        settings = AgentSettings(PROTECTED_PATHS="C:\\data,D:\\secrets")
        paths = settings.protected_path_list
        assert len(paths) == 2

    def test_empty_protected_paths(self) -> None:
        """Empty protected paths returns empty list."""
        settings = AgentSettings(PROTECTED_PATHS="")
        assert settings.protected_path_list == []

    def test_server_url_trailing_slash_stripped(self) -> None:
        """Trailing slash is stripped from server URL."""
        settings = AgentSettings(SERVER_URL="http://localhost:8000/")
        assert not settings.SERVER_URL.endswith("/")


class TestAgentLifecycle:
    """Tests for agent startup and shutdown."""

    def test_agent_initializes(self) -> None:
        """Agent initializes without error."""
        settings = AgentSettings()
        agent = SentinelAgent(settings)
        assert agent.device_id == settings.DEVICE_ID
        assert not agent.is_running

    def test_agent_starts_and_stops(self) -> None:
        """Agent starts and shuts down cleanly."""
        settings = AgentSettings()
        agent = SentinelAgent(settings)

        async def run_test() -> None:
            # Start agent in background
            task = asyncio.create_task(agent.start())

            # Give it a moment to start
            await asyncio.sleep(0.1)
            assert agent.is_running

            # Trigger shutdown
            agent._shutdown_event.set()
            await task

            assert not agent.is_running

        asyncio.run(run_test())
