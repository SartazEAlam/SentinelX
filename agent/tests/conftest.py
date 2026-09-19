"""Shared test fixtures for agent tests."""

from pathlib import Path

import pytest
from sentinel_agent.config import AgentSettings


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def agent_settings(tmp_dir: Path) -> AgentSettings:
    """Agent settings pointing to a temp identity dir."""
    return AgentSettings(
        SERVER_URL="http://localhost:8000",
        DEVICE_ID="test-device-001",
        API_TOKEN="test-token-123",
        IDENTITY_DIR=str(tmp_dir / ".sentinelx"),
        PROTECTED_PATHS=str(tmp_dir / "protected"),
        HEARTBEAT_INTERVAL_SECONDS=5,
        BATCH_FLUSH_INTERVAL_SECONDS=1,
        BATCH_SIZE=10,
    )
