"""Tests for agent configuration and lifecycle."""

import pytest
from sentinel_agent.agent import AgentState, SentinelAgent
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

    def test_new_settings_have_defaults(self) -> None:
        """Phase 2 settings have sensible defaults."""
        settings = AgentSettings()
        assert settings.HEARTBEAT_INTERVAL_SECONDS == 60
        assert settings.BATCH_SIZE == 50
        assert settings.BATCH_FLUSH_INTERVAL_SECONDS == 10
        assert settings.MAX_RETRY_ATTEMPTS == 3
        assert settings.FILE_HASH_ENABLED is True
        assert settings.FILE_HASH_MAX_SIZE_MB == 50
        assert settings.USB_POLL_INTERVAL_SECONDS == 5

    def test_excluded_extensions_parsing(self) -> None:
        """Excluded extensions are parsed into a set."""
        settings = AgentSettings(EXCLUDED_EXTENSIONS=".tmp,.log,.lock")
        exts = settings.excluded_extension_set
        assert ".tmp" in exts
        assert ".log" in exts
        assert ".lock" in exts

    def test_excluded_directories_parsing(self) -> None:
        """Excluded directories are parsed into a set."""
        settings = AgentSettings(EXCLUDED_DIRECTORIES=".git,node_modules")
        dirs = settings.excluded_directory_set
        assert ".git" in dirs
        assert "node_modules" in dirs

    def test_identity_path(self) -> None:
        """Identity path resolves to an absolute path."""
        settings = AgentSettings(IDENTITY_DIR="~/.sentinelx")
        assert settings.identity_path.is_absolute()

    def test_file_hash_max_bytes(self) -> None:
        """File hash max bytes computed from MB setting."""
        settings = AgentSettings(FILE_HASH_MAX_SIZE_MB=100)
        assert settings.file_hash_max_bytes == 100 * 1024 * 1024


class TestAgentLifecycle:
    """Tests for agent startup and shutdown."""

    def test_agent_initializes(self) -> None:
        """Agent initializes without error."""
        settings = AgentSettings()
        agent = SentinelAgent(settings)
        assert not agent.is_running
        assert agent.state == AgentState.STOPPED

    def test_agent_state_enum(self) -> None:
        """AgentState enum has all expected values."""
        states = {s.value for s in AgentState}
        assert "INITIALIZING" in states
        assert "REGISTERING" in states
        assert "RUNNING" in states
        assert "DEGRADED" in states
        assert "STOPPING" in states
        assert "STOPPED" in states
